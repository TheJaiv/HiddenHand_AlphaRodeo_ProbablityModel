"""heist/fit_opp.py - fit opp_core parameters to one team entry's public replays.

    python3 -I heist/fit_opp.py "Team Name" ENTRY [--iters 3000] [--seed 1] [--fix K=V ...]

Every cached fight of the entry is replayed from the team's seat with the real history, and a
parameter set is scored by how closely it reproduces the team's own decisions:
    quote error (median-ish: mean of min(|err|, 8)), response mismatches, move mismatches.
Prints the best parameter sets and their agreement. Fit only describes deal 1 (the only deal the
arena shows); live scores are checked separately (heist/calib.py).
"""
from __future__ import annotations

import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from rules import Obs          # noqa: E402
from opp_core import make_bot, DEFAULT   # noqa: E402

RANK = {"A": 1, "J": 11, "Q": 12, "K": 13}
DATA = os.path.join(HERE, "data", "fights")


def rk(c):
    v = c.strip()[:-1]
    return RANK.get(v) or int(v)


def decisions(play, i):
    """[(kind, obs, real, extra)] for seat i of one replayed play, built from the real history."""
    hands = [list(play["hands"][0]), list(play["hands"][1])]
    board = play["board"]
    peeked = [set(), set()]
    pos, cash, spent = [0, 0], [0.0, 0.0], [0.0, 0.0]
    tape, discards, peeks = [], [], []
    out = []

    def obs(s, rnd, shown):
        me, opp = hands[s], hands[1 - s]
        who = lambda x: "me" if x == s else "opp"
        known = set(me) | set(board[:shown]) | {c for _, _, c in discards} | peeked[s]
        unseen = [4] * 13
        for c in known:
            unseen[rk(c) - 1] -= 1
        return Obs(round=rnd, hand=tuple(rk(c) for c in me), board=tuple(rk(c) for c in board[:shown]),
                   opp_known=tuple(rk(c) for c in opp if c in peeked[s]), unseen=tuple(unseen),
                   position=pos[s], cash=cash[s], spent=spent[s],
                   tape=tuple((r, who(m), px, q) for r, m, px, q in tape),
                   discards=tuple((r, who(x), rk(c)) for r, x, c in discards),
                   peeks=tuple((r, who(x)) for r, x in peeks))

    for row in play["rounds"]:
        rnd = row["round"]
        shown = rnd - 1
        o = obs(i, rnd, shown)
        real = row["moves"][i]
        real_mv = None if real is None else ("PEEK" if real["kind"] == "peek" else ("SWAP", rk(real["out"])))
        out.append(("move", o, real_mv, None))
        for s in (0, 1):
            m = row["moves"][s]
            if m and m["kind"] == "peek":
                if m.get("card"):
                    peeked[s].add(m["card"])
                spent[s] += 3.0
                peeks.append((rnd, s))
        for s in (0, 1):
            m = row["moves"][s]
            if m and m["kind"] == "swap":
                h = hands[s]
                h[h.index(m["out"])] = m["in"]
                discards.append((rnd, s, m["out"]))
        for q in row["quotes"]:
            mk = q["maker"]
            tk = 1 - mk
            if mk == i:
                if not q["auto"]:
                    out.append(("quote", obs(i, rnd, shown), q["price"], None))
            else:
                out.append(("respond", obs(i, rnd, shown), q["qty"], (q["price"], pos[tk], pos[mk])))
            qty = q["qty"]
            if qty:
                fill = q["price"] + 2 if qty > 0 else q["price"] - 2
                pos[tk] += qty
                cash[tk] -= qty * fill
                pos[mk] -= qty
                cash[mk] += qty * fill
            tape.append((rnd, mk, q["price"], qty))
    return out


def load(team, entry):
    plays = []
    for fn in sorted(os.listdir(DATA)):
        d = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
        ids = {d["a"]: d["a_id"], d["b"]: d["b_id"]}
        if ids.get(team) != entry:
            continue
        for p in d["plays"]:
            plays.append(decisions(p, p["seats"].index(team)))
    return plays


def evaluate(P, plays, detail=False):
    B = make_bot(P)
    qe = []
    rm = rn = mm = mn = 0
    for dec in plays:
        bot = B()
        for kind, o, real, extra in dec:
            try:
                if kind == "move":
                    mv = bot.move(o)
                    if isinstance(mv, tuple):
                        mv = ("SWAP", o.hand[mv[1]])
                    mn += 1
                    mm += mv != real
                elif kind == "quote":
                    q = round(bot.quote(o), 2)
                    qe.append(min(abs(q - real), 8.0))
                else:
                    price, tpos, mpos = extra
                    r = max(-2, min(2, int(bot.respond(o, price))))
                    r = max(-10 - tpos, mpos - 10, min(r, 10 - tpos, mpos + 10))
                    rn += 1
                    rm += r != real
            except Exception:
                if kind == "quote":
                    qe.append(8.0)
                elif kind == "respond":
                    rn += 1
                    rm += 1
                else:
                    mn += 1
                    mm += 1
    q = sum(qe) / max(len(qe), 1)
    r = rm / max(rn, 1)
    m = mm / max(mn, 1)
    loss = q + 6.0 * r + 3.0 * m
    if detail:
        return loss, q, r, m, len(qe), rn, mn
    return loss


SPACE = {
    "FQ": (-3.0, 7.0), "H1": (0.0, 1.0), "T": (0.0, 1.0), "SANE": (5.0, 60.0), "TL": (-1.0, 3.0),
    "SA": (0.0, 1.2), "W": (0.0, 1.0), "C": (-3.5, 3.5), "CSIGN": (0, 1), "HIDE": (-0.5, 1.0),
    "QA": (-3.0, 3.0), "SKEW": (-0.5, 1.5), "TP": (0, 1), "TH": (0.0, 7.0), "TH2": (0.0, 9.0),
    "SANR": (10.0, 120.0), "RS": (1, 5), "SG": (0.0, 5.0),
}
INTS = {"CSIGN", "TP", "RS"}


def rand_p(rng, fix):
    P = {}
    for k, (a, b) in SPACE.items():
        if k in fix:
            P[k] = fix[k]
        elif k in INTS:
            P[k] = rng.randint(a, b)
        else:
            P[k] = rng.uniform(a, b)
    if P["TH2"] < P["TH"]:
        P["TH2"] = P["TH"]
    return P


def perturb(rng, P, fix, scale):
    Q = dict(P)
    for k in rng.sample(list(SPACE), 3):
        if k in fix:
            continue
        a, b = SPACE[k]
        if k in INTS:
            Q[k] = rng.randint(a, b)
        else:
            Q[k] = min(b, max(a, Q[k] + rng.gauss(0, scale * (b - a))))
    if Q["TH2"] < Q["TH"]:
        Q["TH2"] = Q["TH"]
    return Q


def fit(team, entry, iters=3000, seed=1, fix=None, verbose=True):
    fix = fix or {}
    plays = load(team, entry)
    rng = random.Random(seed)
    best = []
    for _ in range(iters // 3):
        P = rand_p(rng, fix)
        best.append((evaluate(P, plays), P))
    best.sort(key=lambda x: x[0])
    best = best[:12]
    for it in range(iters - iters // 3):
        L, P = best[it % len(best)]
        Q = perturb(rng, P, fix, 0.15 if it < iters // 2 else 0.05)
        LQ = evaluate(Q, plays)
        if LQ < best[-1][0]:
            best[-1] = (LQ, Q)
            best.sort(key=lambda x: x[0])
    if verbose:
        print(f"{team} #{entry}: {len(plays)} plays")
        for L, P in best[:3]:
            l, q, r, m, nq, nr, nm = evaluate(P, plays, detail=True)
            print(f"  loss {l:.3f}: quote err {q:.2f} (n {nq}), respond miss {r:.2f} (n {nr}), move miss {m:.2f} (n {nm})")
            print("   ", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in P.items()})
    return best, plays


if __name__ == "__main__":
    args = sys.argv[1:]
    fix = {}
    if "--fix" in args:
        k = args.index("--fix")
        for kv in args[k + 1:]:
            if "=" not in kv:
                break
            a, b = kv.split("=")
            fix[a] = float(b) if "." in b else int(b)
    iters = int(args[args.index("--iters") + 1]) if "--iters" in args else 3000
    seed = int(args[args.index("--seed") + 1]) if "--seed" in args else 1
    fit(args[0], int(args[1]), iters, seed, fix)
