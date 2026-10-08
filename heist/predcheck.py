"""heist/predcheck.py - does the field model predict per-team LIVE changes between two of our files?

    python3 heist/predcheck.py NEW.py OLD.py NEW_ENTRY OLD_ENTRY [--seeds 10 11] [--deals 800]
For every imitation in data/fits.json whose team entry fought both live entries: local diff vs live diff.
"""
import argparse
import json
import math
import os
import statistics as S
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import feval   # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("new")
    ap.add_argument("old")
    ap.add_argument("en")
    ap.add_argument("eo")
    ap.add_argument("--seeds", type=int, nargs="+", default=[10, 11])
    ap.add_argument("--deals", type=int, default=800)
    a = ap.parse_args()
    m = json.load(open(os.path.join(HERE, "data", "matrix.json")))
    fits = json.load(open(os.path.join(HERE, "data", "fits.json")))
    o = m["ours"]
    rows = []
    opps = []
    for team, d in fits.items():
        key = f"{team}#{d['entry']}"
        if key in o.get(a.en, {}) and key in o.get(a.eo, {}):
            opps.append((team, os.path.join(KIT, d["file"]), o[a.en][key] - o[a.eo][key]))
    bots = [os.path.abspath(a.new), os.path.abspath(a.old)]
    M = feval.matrix(bots, [p for _, p, _ in opps], a.seeds, a.deals, 8)
    for team, p, live in opps:
        loc = feval.score(M[(bots[0], p)])[0] - feval.score(M[(bots[1], p)])[0]
        rows.append((team, loc, live))
    xs = [r[1] for r in rows]
    ys = [r[2] for r in rows]
    mx, my = S.mean(xs), S.mean(ys)
    r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    print(f"{os.path.basename(a.new)} - {os.path.basename(a.old)}: {len(rows)} teams; local mean {mx:+.2f}, live mean {my:+.2f}, corr {r:+.2f}")
    for t, l, v in sorted(rows, key=lambda x: x[2]):
        print(f"  {t:<22} local {l:+6.2f}  live {v:+6.2f}  {'OK' if (l > 0) == (v > 0) else 'SIGN'}")


if __name__ == "__main__":
    main()
