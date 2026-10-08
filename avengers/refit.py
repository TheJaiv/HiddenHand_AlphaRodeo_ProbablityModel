"""avengers/refit.py - refit opp_core params for the teams that matter (newest entries), save to data/refits.json.

    python3 -I avengers/refit.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "heist"))
from fit_opp import fit  # noqa: E402

TEAMS = [
    ("Cyberpsycho", 316), ("Quants Treasure", 480), ("Godtier", 465),
    ("Trade Transmitters", 371), ("Imposters", 457), ("Happy Happy", 496),
    ("Techy Traders", 502), ("Chill Chips", 493), ("KRYPTEX", 503),
    ("Team How", 500),
]


def main():
    out = {}
    for team, entry in TEAMS:
        print(f"=== {team} #{entry}", flush=True)
        best, plays = fit(team, entry, iters=2400, seed=2)
        L, P = best[0]
        out[team] = {"entry": entry, "plays": len(plays), "loss": L, "P": P}
        print(json.dumps(P), flush=True)
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, "data", "refits.json"), "w"), indent=1)
    print("saved avengers/data/refits.json")


if __name__ == "__main__":
    main()
