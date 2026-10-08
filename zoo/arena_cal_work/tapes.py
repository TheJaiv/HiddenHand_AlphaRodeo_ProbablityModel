"""Turn arena_raw fight JSON into per-decision records, with Obs rebuilt as the engine would.

Each record is one decision of the TEAM: (kind, obs, actual), kind in move/quote/respond,
with the full history of both sides up to that point (teacher forcing).
"""
import glob
import json
import os
import sys

R = "/Users/jaiv/Coding/hiddenhand/tqc-hiddenhand-moneyheist"
sys.path.insert(0, R)
from rules import Obs  # noqa: E402

RANK = {"A": 1, "J": 11, "Q": 12, "K": 13}


def rk(c):
    v = c[:-1]
    return RANK.get(v) or int(v)


def load(team_dir, entry=None, team_name=None):
    """Saved fights; with entry, only those where team_name played as that entry id."""
    out, seen = [], set()
    for fn in sorted(glob.glob(os.path.join(R, "zoo/arena_raw", team_dir, "*.json"))):
        base = os.path.basename(fn)
        if base.startswith("_"):
            continue
        d = json.load(open(fn))
        if entry is not None and d.get("entry_ids", {}).get(team_name) != entry:
            continue
        if d["href"] in seen:
            continue
        seen.add(d["href"])
        out.append((base, d))
    return out


def decisions(play, me):
    """Yield (kind, obs, actual, extra) for seat `me` in one recorded play."""
    seats = play["seats"]
    hands = [list(h) for h in play["hands"]]   # card strings, so suits keep cards distinct
    board = play["board"]
    peeked = [set(), set()]
    tape, discards, peeks = [], [], []
    pos = [0, 0]
    cash = [0.0, 0.0]
    spent = [0.0, 0.0]
    qctx = []   # every quote so far, with MY view when it was made: (round, maker, price, B, nb, m, H)

    def obs(i, rnd, shown):
        opp = 1 - i
        known = set(hands[i]) | set(board[:shown]) | {c for _, _, c in discards} | peeked[i]
        unseen = [4] * 13
        for c in known:
            unseen[rk(c) - 1] -= 1
        who = lambda s: "me" if s == i else "opp"
        return Obs(round=rnd, hand=tuple(rk(c) for c in hands[i]),
                   board=tuple(rk(c) for c in board[:shown]),
                   opp_known=tuple(rk(c) for c in hands[opp] if c in peeked[i]),
                   unseen=tuple(unseen), position=pos[i], cash=cash[i], spent=spent[i],
                   tape=tuple((r, who(m), px, q) for r, m, px, q in tape),
                   discards=tuple((r, who(s), rk(c)) for r, s, c in discards),
                   peeks=tuple((r, who(s)) for r, s in peeks))

    for row in play["rounds"]:
        rnd = row["round"]
        shown = rnd - 1
        o = obs(me, rnd, shown)
        mv = row["moves"][me]
        if mv is None:
            act = None
        elif mv["kind"] == "peek":
            act = "PEEK"
        else:
            act = ("SWAP", hands[me].index(mv["out"]))
        yield "move", o, act, {"round": rnd, "qctx": tuple(qctx)}
        # apply moves: peeks first, then swaps (as the engine does)
        for i in (0, 1):
            m = row["moves"][i]
            if m and m["kind"] == "peek":
                if m.get("card"):
                    peeked[i].add(m["card"])
                spent[i] += 3.0
                peeks.append((rnd, i))
        for i in (0, 1):
            m = row["moves"][i]
            if m and m["kind"] == "swap":
                j = hands[i].index(m["out"])
                hands[i][j] = m["in"]
                discards.append((rnd, i, m["out"]))
        for q in row["quotes"]:
            mk = q["maker"]
            o_now = obs(me, rnd, shown)
            m_now = sum((r + 1) * c for r, c in enumerate(o_now.unseen)) / sum(o_now.unseen)
            here = (rnd, "me" if mk == me else "opp", q["price"], sum(o_now.board), len(o_now.board),
                    m_now, sum(o_now.hand))
            if mk == me:
                yield "quote", o_now, (None if q["auto"] else q["price"]), {"round": rnd, "qctx": tuple(qctx)}
            else:
                yield "respond", o_now, q["qty"], {"round": rnd, "price": q["price"], "qctx": tuple(qctx),
                                                    "here": here}
            qctx.append(here + (q["qty"],))
            qty = q["qty"]
            if qty:
                fill = q["price"] + 2 if qty > 0 else q["price"] - 2
                tk = 1 - mk
                pos[tk] += qty
                cash[tk] -= qty * fill
                pos[mk] -= qty
                cash[mk] += qty * fill
            tape.append((rnd, mk, q["price"], qty))


def team_decisions(team_dir, team_name, entry=None):
    """All decisions of team_name across its saved fights: list of (fight, seat, kind, obs, act, extra)."""
    out = []
    for base, d in load(team_dir, entry, team_name):
        for p in d["plays"]:
            if team_name not in p["seats"]:
                continue
            me = p["seats"].index(team_name)
            opp = p["seats"][1 - me]
            for kind, o, act, ex in decisions(p, me):
                ex = dict(ex, fight=base, opp=opp, seat=me)
                out.append((kind, o, act, ex))
    return out
