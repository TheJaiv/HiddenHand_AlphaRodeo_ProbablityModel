"""heist/follow.py - how each team's quotes relate to the opponent's last quote (all cached replays).

Per (team, entry): for every quote it makes after the opponent has quoted in the deal,
  d_opp  = its quote - the opponent's last quote (carried: + board cards turned since, minus 7 each... not applied)
  d_fair = its quote - its own naive fair (hand + board + unknowns x unseen average)
Prints mean / sd of both, and the share of quotes with |d_opp| < 1.6 (follower) - over all its fights.
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


stats = defaultdict(lambda: {"dopp": [], "dfair": [], "first": [], "fights": set(), "r1second": []})
for fn in os.listdir(DATA):
    d = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
    ids = {d["a"]: d["a_id"], d["b"]: d["b_id"]}
    for p in d["plays"]:
        for i in (0, 1):
            team = p["seats"][i]
            key = (team, ids[team])
            st = stats[key]
            st["fights"].add(fn)
            hand = [rk(c) for c in p["hands"][i]]
            board = p["board_ranks"]
            disc = []
            opp_last = None
            for row in p["rounds"]:
                r = row["round"]
                for j, mv in enumerate(row["moves"]):
                    if mv and mv["kind"] == "swap":
                        disc.append(rk(mv["out"]))
                        if j == i:
                            hand[hand.index(rk(mv["out"]))] = rk(mv["in"])
                shown = board[:r - 1]
                unseen = [4] * 13
                for c in hand + shown + disc:
                    unseen[c - 1] -= 1
                m = sum((k + 1) * c for k, c in enumerate(unseen)) / sum(unseen)
                fair = sum(hand) + sum(shown) + (10 - len(shown)) * m
                for qi, q in enumerate(row["quotes"]):
                    if q["maker"] == i:
                        if opp_last is None:
                            st["first"].append(q["price"] - fair)
                        else:
                            st["dopp"].append(q["price"] - opp_last)
                            if r == 1:
                                st["r1second"].append(q["price"] - opp_last)
                        st["dfair"].append(q["price"] - fair)
                    else:
                        opp_last = q["price"]
rows = []
for (team, e), st in stats.items():
    if len(st["dopp"]) < 20:
        continue
    do = st["dopp"]
    near = sum(abs(x) < 1.6 for x in do) / len(do)
    rows.append((near, team, e, len(st["fights"]), S.mean(do), S.pstdev(do), S.mean(st["dfair"]), S.pstdev(st["dfair"]),
                 S.mean(st["r1second"]) if st["r1second"] else 0, S.pstdev(st["r1second"]) if st["r1second"] else 0))
rows.sort(reverse=True)
print(f"{'team':<22}{'entry':>6}{'fights':>7}{'near':>6}{'d_opp':>8}{'sd':>6}{'d_fair':>8}{'sd':>6}{'r1sec':>8}{'sd':>6}")
for near, team, e, nf, mo, so, mf, sf, r1, r1s in rows:
    print(f"{team:<22}{e:>6}{nf:>7}{near:>6.2f}{mo:>+8.2f}{so:>6.2f}{mf:>+8.2f}{sf:>6.2f}{r1:>+8.2f}{r1s:>6.2f}")
