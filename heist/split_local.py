"""heist/split_local.py - local PnL split of BOT vs OPP by role (maker/taker), round and swap.

    python3 heist/split_local.py BOT.py OPP.py [--deals 300] [--seed 4]
"""
import argparse
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from bot_loader import load_for_testing   # noqa: E402
from engine import derive_seed, play_deal, rank   # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("bot")
ap.add_argument("opp")
ap.add_argument("--deals", type=int, default=300)
ap.add_argument("--seed", type=int, default=4)
a = ap.parse_args()
B = load_for_testing(a.bot, quiet=True)
O = load_for_testing(a.opp, quiet=True)
acc = defaultdict(float)
n = 0
for d in range(a.deals):
    s = derive_seed(a.seed, d)
    for seat in (0, 1):
        random.seed(derive_seed(a.seed, "rng", 2 * d + seat))
        bots = (B(), O()) if seat == 0 else (O(), B())
        res = play_deal(*bots, s)
        log = res["log"]
        V = log["V"]
        for row in log["rounds"]:
            for q in row["quotes"]:
                if not q["qty"]:
                    continue
                fill = q["price"] + 2 if q["qty"] > 0 else q["price"] - 2
                taker_pnl = q["qty"] * (V - fill)
                if q["maker"] == seat:
                    acc[("maker", row["round"])] -= taker_pnl
                else:
                    acc[("taker", row["round"])] += taker_pnl
        # swap value: my final position x (in - out) if I swapped
        for row in log["rounds"]:
            mv = row["moves"][seat]
            if mv and mv["kind"] == "swap":
                acc[("swap", row["round"])] += log["positions"][seat] * (rank(mv["in"]) - rank(mv["out"]))
            mo = row["moves"][1 - seat]
            if mo and mo["kind"] == "swap":
                acc[("their swap", row["round"])] -= log["positions"][1 - seat] * (rank(mo["in"]) - rank(mo["out"]))
        acc["total"] += res["pnl"][seat]
        n += 1
print(f"{os.path.basename(a.bot)} vs {os.path.basename(a.opp)}: {n} plays, PnL per play")
for k in ("maker", "taker", "swap", "their swap"):
    print(f"  {k:<10} " + "  ".join(f"r{r} {acc[(k, r)] / n:+6.2f}" for r in range(1, 6)) +
          f"   sum {sum(acc[(k, r)] for r in range(1, 6)) / n:+6.2f}")
print(f"  total {acc['total'] / n:+.2f}")
