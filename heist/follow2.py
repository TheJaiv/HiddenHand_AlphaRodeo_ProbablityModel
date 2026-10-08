"""heist/follow2.py - per team: regress (its quote - opponent's last quote) on its own hand sum.

A follower: slope ~0 (its quote ignores its hand). An honest reader with trust ~1: slope ~1.
Uses every quote made after the opponent quoted in the same or earlier round, board-carried:
the opponent's last quote is moved by (card - 7) for each board card turned since it was made.
"""
import json
import os
import statistics as S
from collections import defaultdict

RK = {"A": 1, "J": 11, "Q": 12, "K": 13}
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fights")


def rk(c):
    v = c.strip()[:-1]
    return RK.get(v) or int(v)


pts = defaultdict(list)
nf = defaultdict(set)
for fn in os.listdir(DATA):
    d = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
    ids = {d["a"]: d["a_id"], d["b"]: d["b_id"]}
    for p in d["plays"]:
        for i in (0, 1):
            team = p["seats"][i]
            key = (team, ids[team])
            nf[key].add(fn)
            hand = [rk(c) for c in p["hands"][i]]
            board = p["board_ranks"]
            opp_last = None
            opp_round = None
            for row in p["rounds"]:
                r = row["round"]
                for j, mv in enumerate(row["moves"]):
                    if mv and mv["kind"] == "swap" and j == i:
                        hand[hand.index(rk(mv["out"]))] = rk(mv["in"])
                for q in row["quotes"]:
                    if q["maker"] == i:
                        if opp_last is not None:
                            carried = opp_last + sum(c - 7 for c in board[opp_round - 1:r - 1])
                            pts[key].append((sum(hand), q["price"] - carried, r))
                    else:
                        opp_last, opp_round = q["price"], r


def ols(xy):
    xs = [x for x, _ in xy]
    ys = [y for _, y in xy]
    mx, my = S.mean(xs), S.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx < 1e-9:
        return None, my, S.pstdev(ys)
    b = sum((x - mx) * (y - my) for x, y in xy) / sxx
    a = my - b * mx
    res = [y - a - b * x for x, y in xy]
    return b, a + b * 35, S.pstdev(res)


rows = []
for key, v in pts.items():
    if len(v) < 15:
        continue
    xy = [(h, y) for h, y, r in v if abs(y) < 30]
    b, c35, sd = ols(xy)
    rows.append((b if b is not None else 9, key, len(nf[key]), c35, sd, len(xy)))
rows.sort()
print(f"{'team':<22}{'entry':>6}{'fights':>7}{'slope':>7}{'off@35':>8}{'resid':>7}{'n':>5}")
for b, (team, e), n, c35, sd, k in rows:
    print(f"{team:<22}{e:>6}{n:>7}{b:>7.2f}{c35:>+8.2f}{sd:>7.2f}{k:>5}")
