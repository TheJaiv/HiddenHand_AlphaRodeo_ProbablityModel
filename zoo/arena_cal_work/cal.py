"""Score our live bots against candidate imitation files (local, from OUR side).

    python cal.py FILE [FILE...] [--deals 500] [--seeds 1 2] [--ours r1 r2 h1 h2]
"""
import os, sys, math, json, argparse
from multiprocessing import Pool
KIT = "/Users/jaiv/Coding/hiddenhand/tqc-hiddenhand-moneyheist"
sys.path.insert(0, KIT); sys.path.insert(0, KIT + "/tools")
import eval as EV

OURS = {"r1": KIT + "/zoo/rival_1.py", "r2": KIT + "/zoo/rival_2.py",
        "h1": KIT + "/versions/hunt_v01.py", "h2": KIT + "/versions/hunt_v02.py",
        "naive": KIT + "/strategies/naive.py", "reader": KIT + "/strategies/reader.py",
        "sharp": KIT + "/strategies/sharp.py"}


def job(j):
    r = EV.run_match(j)
    pairs = EV.pairs_of(r["per_deal"])
    return [EV.ssqrt(p) for p in pairs], r["notes"]


def run(files, ours=("r1", "r2", "h1", "h2"), deals=500, seeds=(1, 2), procs=3):
    jobs = [(OURS.get(o, o), os.path.abspath(f), s, deals) for f in files for o in ours for s in seeds]
    with Pool(procs) as pool:
        res = pool.map(job, jobs)
    out = {}
    for j, (sc, notes) in zip(jobs, res):
        k = (j[1], j[0])
        out.setdefault(k, []).extend(sc)
    table = {}
    for f in files:
        f = os.path.abspath(f)
        table[f] = {}
        for o in ours:
            v = out[(f, OURS.get(o, o))]
            m = sum(v) / len(v)
            sd = (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5
            table[f][o] = (m, 2 * sd / len(v) ** 0.5)
    return table


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--deals", type=int, default=500)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2])
    ap.add_argument("--ours", nargs="+", default=["r1", "r2", "h1", "h2"])
    a = ap.parse_args()
    t = run(a.files, a.ours, a.deals, a.seeds)
    for f, row in t.items():
        print(os.path.basename(f), "  ".join(f"{o} {m:+.2f}({e:.2f})" for o, (m, e) in row.items()))
