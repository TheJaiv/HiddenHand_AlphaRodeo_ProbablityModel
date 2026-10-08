"""heist/match_replay.py - does a bot file make the same decisions as a team in public replays?

    python3 -I heist/match_replay.py BOT.py [--team "Alpha Rodeo"] FIGHT.json ...

For every play (deal 1, both seatings) the team's seat is fed exactly the observations it
had live (rebuilt from the replay), and the file's move / quote / respond are compared with
what the team really did. Prints agreed / total decisions per fight. 100% on several fights
means the file IS (behaves exactly like) that upload.
"""

from __future__ import annotations

import json
import os
import sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

from bot_loader import load_for_testing   # noqa: E402
from rules import Obs                     # noqa: E402

RANK = {"A": 1, "J": 11, "Q": 12, "K": 13}


def rk(c: str) -> int:
    v = c.strip()[:-1]
    return RANK.get(v) or int(v)


def replay_seat(bot_cls, play: dict, i: int, tol: float = 0.011):
    """Re-run seat i of one play with a fresh bot; return (agree, total, first disagreement)."""
    bot = bot_cls()
    hands = [list(play["hands"][0]), list(play["hands"][1])]
    board = play["board"]
    peeked = [set(), set()]
    pos, cash, spent = [0, 0], [0.0, 0.0], [0.0, 0.0]
    tape, discards, peeks = [], [], []
    agree = total = 0
    first_bad = None

    def obs(s, rnd, shown):
        me = hands[s]
        opp = hands[1 - s]
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

    def check(kind, mine, real, rnd):
        nonlocal agree, total, first_bad
        total += 1
        if kind == "quote":
            ok = abs(mine - real) <= tol
        else:
            ok = mine == real
        if ok:
            agree += 1
        elif first_bad is None:
            first_bad = (rnd, kind, mine, real)

    for row in play["rounds"]:
        rnd = row["round"]
        shown = rnd - 1
        # moves, chosen together on the same pre-move observations
        o = obs(i, rnd, shown)
        try:
            mv = bot.move(o)
        except Exception as e:
            mv = ("ERR", str(e))
        real = row["moves"][i]
        if isinstance(mv, (tuple, list)) and len(mv) == 2 and str(mv[0]).upper() == "SWAP":
            mine_mv = ("SWAP", o.hand[int(mv[1])])
        elif isinstance(mv, str) and mv.upper() == "PEEK":
            mine_mv = "PEEK"
        else:
            mine_mv = None
        real_mv = None if real is None else ("PEEK" if real["kind"] == "peek" else ("SWAP", rk(real["out"])))
        check("move", mine_mv, real_mv, rnd)
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
                try:
                    p = bot.quote(obs(i, rnd, shown))
                    p = min(195.0, max(0.0, round(float(p), 2)))
                except Exception:
                    p = -1.0
                if not q["auto"]:
                    check("quote", p, q["price"], rnd)
            else:
                try:
                    r = int(bot.respond(obs(i, rnd, shown), q["price"]))
                    r = max(-2, min(2, r))
                    L = 10
                    r = max(-L - pos[tk], pos[mk] - L, min(r, L - pos[tk], pos[mk] + L))
                except Exception:
                    r = 99
                check("respond", r, q["qty"], rnd)
            qty = q["qty"]
            if qty:
                fill = q["price"] + 2 if qty > 0 else q["price"] - 2
                pos[tk] += qty
                cash[tk] -= qty * fill
                pos[mk] -= qty
                cash[mk] += qty * fill
            tape.append((rnd, mk, q["price"], qty))
    return agree, total, first_bad


def main() -> int:
    args = sys.argv[1:]
    team = "Alpha Rodeo"
    if "--team" in args:
        k = args.index("--team")
        team = args[k + 1]
        del args[k:k + 2]
    bot_cls = load_for_testing(args[0], quiet=True)
    A = T = 0
    for fn in args[1:]:
        f = json.load(open(fn, encoding="utf-8"))
        a = t = 0
        bads = []
        for play in f["plays"]:
            if team not in play["seats"]:
                continue
            ag, tot, bad = replay_seat(bot_cls, play, play["seats"].index(team))
            a += ag
            t += tot
            if bad:
                bads.append(bad)
        A += a
        T += t
        opp = f["b"] if f["a"] == team else f["a"]
        print(f"  {os.path.basename(fn):<16} vs {opp:<22} {a:3d}/{t:<3d}" + (f"  first miss {bads[0]}" if bads else ""))
    print(f"{os.path.basename(args[0])}: {A}/{T} decisions agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
