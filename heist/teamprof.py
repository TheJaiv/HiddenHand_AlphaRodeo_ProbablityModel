"""heist/teamprof.py - one team entry's behaviour in every cached fight (deal 1, both seats).

    python3 -I heist/teamprof.py "Techy Traders" 482 [--full]

Per play: its hand, its quotes with (quote - its naive fair) and (quote - opponent's last quote, board-carried),
its responses with (its naive fair - price), moves. Then summary lines.
"""
import json
import os
import statistics as S
import sys

RK = {"A": 1, "J": 11, "Q": 12, "K": 13}
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fights")


def rk(c):
    v = c.strip()[:-1]
    return RK.get(v) or int(v)


team, E = sys.argv[1], int(sys.argv[2])
full = "--full" in sys.argv
first_q = {32: [], 40: []}
resp = []        # (round, edge_naive, qty, hand)
rows_q = []      # (round, hand, q - fair, q - oppcarried)
moves = []
scores = []
for fn in sorted(os.listdir(DATA)):
    d = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
    ids = {d["a"]: d["a_id"], d["b"]: d["b_id"]}
    if ids.get(team) != E:
        continue
    opp = d["b"] if d["a"] == team else d["a"]
    sc = d["score_a"] if d["a"] == team else d["score_b"]
    scores.append((sc, opp))
    for p in d["plays"]:
        i = p["seats"].index(team)
        hand = [rk(c) for c in p["hands"][i]]
        h0 = sum(hand)
        board = p["board_ranks"]
        disc = []
        peeked = []
        opp_last = None
        opp_round = None
        line = []
        for row in p["rounds"]:
            r = row["round"]
            for j, mv in enumerate(row["moves"]):
                if mv and mv["kind"] == "swap":
                    disc.append(rk(mv["out"]))
                    if j == i:
                        hand[hand.index(rk(mv["out"]))] = rk(mv["in"])
                        moves.append(f"s{r}")
                        line.append(f"[swap {mv['out']}->{mv['in']}]")
                    else:
                        line.append(f"[opp swap {mv['out']}]")
                if mv and mv["kind"] == "peek":
                    if j == i:
                        moves.append(f"p{r}")
                        line.append(f"[peek {mv.get('card')}]")
                        if mv.get("card"):
                            peeked.append(rk(mv["card"]))
                    else:
                        line.append("[opp peek]")
            shown = board[:r - 1]
            unseen = [4] * 13
            for c in hand + shown + disc + peeked:
                unseen[c - 1] -= 1
            m = sum((k + 1) * c for k, c in enumerate(unseen)) / sum(unseen)
            fair = sum(hand) + sum(shown) + sum(peeked) + (10 - len(shown) - len(peeked)) * m
            for q in row["quotes"]:
                if q["maker"] == i:
                    oc = None if opp_last is None else opp_last + sum(c - 7 for c in board[opp_round - 1:r - 1])
                    if opp_last is None and r == 1:
                        first_q[h0].append(q["price"] - fair)
                    rows_q.append((r, h0, q["price"] - fair, None if oc is None else q["price"] - oc))
                    line.append(f"r{r} Q{q['price']:.2f}(f{q['price'] - fair:+.1f}" +
                                ("" if oc is None else f",o{q['price'] - oc:+.1f}") + f")->{q['qty']:+d}")
                else:
                    resp.append((r, fair - q["price"], q["qty"], h0))
                    line.append(f"r{r} R{q['qty']:+d}@{q['price']:.2f}(e{fair - q['price']:+.1f})")
                    opp_last, opp_round = q["price"], r
        if full:
            print(f"{opp[:16]:<16} h{h0} pnl {p['pnl'][i]:+7.1f} | " + " ".join(line))
scores.sort()
print(f"\n{team} #{E}: {len(scores)} fights, mean score {S.mean(s for s, _ in scores):+.2f}")
print("  worst: " + ", ".join(f"{o} {s:+.2f}" for s, o in scores[:6]))
for h in (32, 40):
    if first_q[h]:
        print(f"  first quote (no info), hand {h}: q - naive fair mean {S.mean(first_q[h]):+.2f} sd {S.pstdev(first_q[h]):.2f} n {len(first_q[h])}")
for h in (32, 40):
    for r in range(1, 6):
        v = [(qf, qo) for rr, hh, qf, qo in rows_q if rr == r and hh == h and qo is not None]
        if v:
            print(f"  hand {h} r{r}: q - fair {S.mean(a for a, _ in v):+6.2f} (sd {S.pstdev([a for a, _ in v]):4.2f})"
                  f"   q - opp carried {S.mean(b for _, b in v):+6.2f} (sd {S.pstdev([b for _, b in v]):4.2f})  n {len(v)}")
# response rule: share of buys / sells by naive edge bucket
print("  responses by naive edge (fair - price):")
for lo, hi in ((-99, -6), (-6, -4), (-4, -2), (-2, 0), (0, 2), (2, 4), (4, 6), (6, 99)):
    v = [q for r, e, q, h in resp if lo <= e < hi]
    if v:
        print(f"    edge [{lo:+},{hi:+}): n {len(v):3d}  buy {sum(q > 0 for q in v) / len(v):.2f}  sell {sum(q < 0 for q in v) / len(v):.2f}"
              f"  mean qty {S.mean(v):+.2f}")
from collections import Counter
print("  moves:", Counter(moves).most_common())
