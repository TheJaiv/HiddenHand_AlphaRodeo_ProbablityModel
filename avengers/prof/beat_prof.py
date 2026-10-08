"""avengers/prof/beat_prof.py - dump one team's deal-1 replays (parsed heist fights) as tables.

    python3 -I avengers/prof/beat_prof.py TEAM ENTRY_ID [--vs US_TEAM]

For every cached fight of the team's entry, prints each play's event sequence from the
team's seat: round, board revealed, move, quote (own price | opp price, opp qty, their pos).
Deal 1 hands are always the same (32 vs 40), so what varies between fights is only the
opponent's quotes/trades; that's what reveals how this team reacts.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "heist", "data", "fights")
RANK = {"A": 1, "J": 11, "Q": 12, "K": 13}


def rk(c):
    v = c.strip()[:-1]
    return RANK.get(v) or int(v)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--vs")]
    team, entry = args[0], int(args[1])
    vs = None
    if "--vs" in sys.argv:
        vs = sys.argv[sys.argv.index("--vs") + 1]
    n = 0
    for fn in sorted(os.listdir(DATA)):
        d = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
        ids = {d["a"]: d["a_id"], d["b"]: d["b_id"]}
        if ids.get(team) != entry:
            continue
        n += 1
        for p in d["plays"]:
            i = p["seats"].index(team)
            opp = p["seats"][1 - i]
            if vs and opp != vs:
                continue
            hand = [rk(c) for c in p["hands"][i]]
            print(f"--- fight {d['a_id']} vs {d['b_id']} ({d['a']} vs {d['b']}), seat {team} "
                  f"hand {hand} (sum {sum(hand)}) board {[rk(c) for c in p['board']]} "
                  f"V {p['V']} pnl {p['pnl'][i]} pos {p['positions'][i]}")
            for row in p["rounds"]:
                r = row["round"]
                mv = row["moves"][i]
                mvs = "-"
                if mv:
                    mvs = ("peek" if mv["kind"] == "peek" else
                           f"swap {rk(mv['out'])}->{rk(mv['in'])}")
                print(f"  r{r} board={[rk(c) for c in p['board'][:r - 1]]} me[{mvs}]", end="")
                for q in row["quotes"]:
                    if q["maker"] == i:
                        print(f" | QUOTE {q['price']:>7.2f} <- opp takes {q['qty']:+d}", end="")
                    else:
                        print(f" | opp {q['price']:>7.2f} I take {q['qty']:+d}", end="")
                print()
    print(f"{team} #{entry}: {n} fights")


if __name__ == "__main__":
    main()
