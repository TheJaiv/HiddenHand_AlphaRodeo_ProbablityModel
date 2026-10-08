"""heist/pnlsplit.py - deal-1 PnL split (maker / taker, by round) for a team's fights.

    python3 -I heist/pnlsplit.py TEAM ENTRY
"""
import json
import os
import sys
from collections import defaultdict

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fights")
team, E = sys.argv[1], int(sys.argv[2])
tot = defaultdict(float)
n = 0
rows = []
for fn in sorted(os.listdir(DATA)):
    d = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
    if E not in (d["a_id"], d["b_id"]) or team not in (d["a"], d["b"]):
        continue
    if (d["a"] == team and d["a_id"] != E) or (d["b"] == team and d["b_id"] != E):
        continue
    opp = d["b"] if d["a"] == team else d["a"]
    sc = d["score_a"] if d["a"] == team else d["score_b"]
    mk = tk = 0.0
    for p in d["plays"]:
        i = p["seats"].index(team)
        V = p["V"]
        for r in p["rounds"]:
            for q in r["quotes"]:
                if not q["qty"]:
                    continue
                fill = q["price"] + 2 if q["qty"] > 0 else q["price"] - 2
                taker_pnl = q["qty"] * (V - fill)
                if q["maker"] == i:
                    mk -= taker_pnl
                    tot[("maker", r["round"])] -= taker_pnl
                else:
                    tk += taker_pnl
                    tot[("taker", r["round"])] += taker_pnl
    n += 1
    rows.append((sc, opp, mk, tk))
rows.sort()
for sc, opp, mk, tk in rows:
    print(f"  {opp:<22} live {sc:+6.2f}   deal1 maker {mk:+8.1f} taker {tk:+8.1f}")
print(f"{team} #{E}: {n} fights; deal-1 PnL per fight by role and round:")
for role in ("maker", "taker"):
    print(f"  {role}: " + "  ".join(f"r{r} {tot[(role, r)] / max(n, 1):+6.1f}" for r in range(1, 6))
          + f"   total {sum(tot[(role, r)] for r in range(1, 6)) / max(n, 1):+6.1f}")
