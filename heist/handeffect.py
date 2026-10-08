"""heist/handeffect.py - how much each team's quote moves with its OWN hand (replays show both hands).

For every quote of a team's newest entry: (quote - public estimate) and its current hand sum. Slope of
that on the hand sum = how much of its hand its quotes show: ~0.8 honest, ~0 hider / follower,
negative = quotes against its hand. Also the same slope for its answers (P(buy) - P(sell) per hand point).
"""
import json
import os
import statistics as S
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fit_opp import decisions   # noqa: E402

m = json.load(open(os.path.join(HERE, "data", "matrix.json")))
newest = m["newest"]
D = os.path.join(HERE, "data", "fights")
pts, ans = {}, {}
for fn in os.listdir(D):
    d = json.load(open(os.path.join(D, fn)))
    ids = {d["a"]: d["a_id"], d["b"]: d["b_id"]}
    for p in d["plays"]:
        for i in (0, 1):
            team = p["seats"][i]
            if ids.get(team) != newest.get(team):
                continue
            for kind, o, real, extra in decisions(p, i):
                if o.round == 1:
                    continue
                u = [4] * 13
                for k in o.board:
                    u[k - 1] -= 1
                for _, _, k in o.discards:
                    u[k - 1] -= 1
                pub = sum(o.board) + (15 - len(o.board)) * sum((r + 1) * c for r, c in enumerate(u)) / sum(u)
                h = sum(o.hand)
                if kind == "quote":
                    pts.setdefault(team, []).append((h, real - pub))
                elif kind == "respond":
                    ans.setdefault(team, []).append((h, (1 if real > 0 else -1 if real < 0 else 0), extra[0] - pub))


def slope(xy):
    xs = [x for x, _ in xy]
    ys = [y for _, y in xy]
    mx, my = S.mean(xs), S.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in xy) / sxx if sxx > 1e-9 else float("nan")


rows = []
for t, v in pts.items():
    if len(v) < 20:
        continue
    a = ans.get(t, [])
    rows.append((slope(v), t, len(v), slope([(h, s) for h, s, _ in a]) if len(a) > 10 else float("nan")))
rows.sort()
print(f"{'team':<22}{'quote slope':>12}{'answer slope':>14}{'n':>5}   (quote slope: 0.8 honest, 0 hides, <0 against)")
for s, t, n, a in rows:
    print(f"{t:<22}{s:>12.2f}{a:>14.3f}{n:>5}")
