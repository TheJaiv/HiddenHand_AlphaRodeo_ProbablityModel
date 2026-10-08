"""avengers/calib.py - check an imitation against our live files' live scores.

    python3 -I avengers/calib.py OPP_FILE 'Team Name' --live tokyo:-1.77 nairobi:-1.86 rio:-0.96 [--deals 400]

Runs each of our bot files against OPP_FILE locally and prints live vs local per file
(like heist/calib.py). The imitation calibrates when every local score is within ~1.5
of the live one. Uses the avengers feval cache.
"""
import argparse
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import feval  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("opp", help="imitation file")
    ap.add_argument("team")
    ap.add_argument("--live", nargs="+", help="file:live_score pairs, e.g. tokyo:-1.77")
    ap.add_argument("--deals", type=int, default=400)
    ap.add_argument("--seeds", type=int, nargs="+", default=[4, 5])
    ap.add_argument("--procs", type=int, default=6)
    a = ap.parse_args()
    files, live = {}, {}
    for kv in a.live:
        f, v = kv.split(":")
        files[f], live[f] = os.path.abspath(os.path.join("heist", f + ".py")), float(v)
    if not files:
        files = {n: os.path.abspath(os.path.join("heist", n + ".py"))
                 for n in ("tokyo", "berlin", "nairobi", "rio", "denver")}
    M = feval.matrix(list(files.values()), [os.path.abspath(a.opp)], a.seeds, a.deals, a.procs, verbose=False)
    ss = feval.ss
    print(f"imitation {a.opp} vs our files (seeds {a.seeds}, {a.deals} deals)")
    ok = True
    for name, f in files.items():
        pairs = M[(f, os.path.abspath(a.opp))]
        loc = statistics.mean(ss(p) for p in pairs)
        se = 2 * statistics.stdev(ss(p) for p in pairs) / len(pairs) ** 0.5
        liv = live.get(name)
        d = f"live {liv:+.2f}" if liv is not None else "live n/a"
        print(f"  {name:<12} local {loc:+.2f} +-{se:.2f}   {d}   diff {loc - liv:+.2f}" if liv is not None
              else f"  {name:<12} local {loc:+.2f} +-{se:.2f}   live n/a")
        if liv is not None and abs(loc - liv) > 1.5:
            ok = False
    print("CALIBRATED" if ok else "NOT CALIBRATED")


if __name__ == "__main__":
    main()
