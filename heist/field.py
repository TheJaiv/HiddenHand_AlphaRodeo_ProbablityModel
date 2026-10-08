"""heist/field.py - the calibrated field model: weighted score of bots, and paired diff vs a base.

    python3 heist/field.py BASE.py CAND.py [CAND2.py ...] [--seeds 4 5] [--deals 400]

Opponents: the house bots (each weight 1, as one of ~57 live opponents) and every imitation listed in
heist/data/field.json (file + weight = how many live teams it stands for). The diff is paired deal by deal
(same deals, same opponent), so its +-2se is much tighter than either score's.
"""
import argparse
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import feval   # noqa: E402


FIELD_FILE = os.environ.get("FIELD", "field.json")


def field():
    f = json.load(open(os.path.join(HERE, "data", FIELD_FILE)))
    # since 15:30 on 8 Oct the house bots play no part in the arena score (rules page); HOUSE=1 adds them back
    out = ([(os.path.join(KIT, "strategies", f"{h}.py"), 1.0, h) for h in ("naive", "reader", "sharp")]
           if os.environ.get("HOUSE") == "1" else [])
    for name, d in f.items():
        out.append((os.path.join(KIT, d["file"]), float(d["weight"]), name))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bots", nargs="+")
    ap.add_argument("--seeds", type=int, nargs="+", default=[4, 5])
    ap.add_argument("--deals", type=int, default=400)
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    F = field()
    bots = [os.path.abspath(b) for b in a.bots]
    M = feval.matrix(bots, [o for o, _, _ in F], a.seeds, a.deals, a.procs)
    W = sum(w for _, w, _ in F)
    ss = feval.ss
    base = bots[0]
    print(f"field model: {len(F)} opponents, total weight {W:g}, seeds {a.seeds}, {a.deals} deals")
    print(f"{'opponent':<26}{'w':>4}" + "".join(f"{os.path.basename(b)[:-3][:12]:>13}" for b in bots))
    for o, w, name in F:
        print(f"{name[:25]:<26}{w:>4g}" + "".join(f"{statistics.mean(ss(p) for p in M[(b, o)]):+13.2f}" for b in bots))
    n = len(M[(base, F[0][0])])
    tot = {b: [sum(w * ss(M[(b, o)][i]) for o, w, _ in F) / W for i in range(n)] for b in bots}
    print(f"{'WEIGHTED':<30}" + "".join(f"{statistics.mean(tot[b]):+13.3f}" for b in bots))
    for b in bots[1:]:
        d = [x - y for x, y in zip(tot[b], tot[base])]
        print(f"  {os.path.basename(b)[:-3]} - {os.path.basename(base)[:-3]}: {statistics.mean(d):+.3f} "
              f"+-{2 * statistics.stdev(d) / math.sqrt(len(d)):.3f} (2se, paired over {len(d)} deal pairs)")


if __name__ == "__main__":
    main()
