"""ceval.py (scratch B) - cached tools/eval.py --compare with the round-2 pool.

Same matches as tools/eval.py (imports its run_match, so identical seeding);
per (bot content hash, opponent content hash, seed, deals) results cached on disk.

    python versions/hunt_scratch_B/ceval.py CAND [CAND2 ...] --base versions/hunt_v10.py --seeds 5 6
Prints per-opponent diff, POOL AVERAGE diff +-2se, READER-FAMILY (first 12) diff, and
head to head vs hunt_v10 and hunt_v01 (left out of the pool average).
"""
import argparse
import hashlib
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(KIT))
sys.path.insert(0, str(KIT / "tools"))

import eval as EV  # noqa: E402
from backtester import resolve  # noqa: E402

CACHE = Path(__file__).resolve().parent / "cache"
POOL = ("naive reader sharp zoo/sharp_t05.py zoo/sharp_t10.py zoo/hider.py zoo/liar.py zoo/ai_typical.py "
        "zoo/mid_bayes.py zoo/mid_guard.py zoo/swapper.py zoo/peeker.py zoo/arena_imposters.py "
        "zoo/arena_pokemons.py zoo/arena_sattebaaz.py zoo/arena_quants_treasure.py zoo/arena_outliers.py "
        "zoo/arena_teenpatti_v4.py zoo/arena_paperhands_v5.py zoo/rival_1.py zoo/rival_2.py "
        "zoo/arena_genz7.py zoo/arena_aj_the_trader.py zoo/arena_kryptex.py zoo/arena_quantumlesssss.py").split()
NREADER = 12


def h(path):
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()[:12]


def key(b, o, seed, deals):
    return f"{Path(b).stem}_{h(b)}__{Path(o).stem}_{h(o)}__{seed}_{deals}.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bots", nargs="+")
    ap.add_argument("--base", default="versions/hunt_v10.py")
    ap.add_argument("--vs", nargs="+")
    ap.add_argument("--h2h", nargs="*", default=["versions/hunt_v10.py", "versions/hunt_v01.py"])
    ap.add_argument("--seeds", type=int, nargs="+", default=[5, 6])
    ap.add_argument("--deals", type=int, default=400)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    vs = a.vs or POOL
    opps = [str(resolve(x).resolve()) for x in vs]
    nread = NREADER if not a.vs else 0
    h2h = [str(resolve(x).resolve()) for x in a.h2h]
    base = str(resolve(a.base).resolve())
    bots = [str(resolve(x).resolve()) for x in a.bots]
    jobs = []
    for b in dict.fromkeys([base] + bots):
        for o in opps + [x for x in h2h if x != b]:
            if o == base and b == base:
                continue
            for s in a.seeds:
                if not (CACHE / key(b, o, s, a.deals)).exists():
                    jobs.append((b, o, s, a.deals))
    t0 = time.time()
    if jobs:
        with Pool(min(a.procs, len(jobs))) as pool:
            for job, res in zip(jobs, pool.imap(EV.run_match, jobs)):
                (CACHE / key(*job)).write_text(json.dumps(res))
    print(f"{len(jobs)} matches in {time.time() - t0:.0f}s")

    def pairs(b, o):
        out = []
        for s in a.seeds:
            r = json.loads((CACHE / key(b, o, s, a.deals)).read_text())
            out += EV.pairs_of(r["per_deal"])
        return out

    for b in bots:
        print(f"\n=== {Path(b).stem} - {Path(base).stem}, seeds {a.seeds}, {a.deals} deals ===")
        drows, nrows = [], []
        for o in opps:
            nb, ob = pairs(b, o), pairs(base, o)
            d = EV.diff_row(nb, ob)
            drows.append(d)
            nrows.append(EV.row_of(nb))
            if not a.quiet:
                sn = EV.stats(EV.row_of(nb))
                so = EV.stats(EV.row_of(ob))
                sd = EV.stats(d)
                print(f"  {Path(o).stem:<24} new {sn[0]:+7.3f}  old {so[0]:+7.3f}  diff {sd[0]:+7.3f} +-{sd[1]:.3f}")
        sd = EV.stats(EV.mix(drows, [1.0] * len(drows)))
        sn = EV.stats(EV.mix(nrows, [1.0] * len(nrows)))
        print(f"  {'POOL AVERAGE':<24} new {sn[0]:+7.3f}  diff {sd[0]:+7.3f} +-{sd[1]:.3f}")
        if nread:
            sr = EV.stats(EV.mix(drows[:nread], [1.0] * nread))
            si = EV.stats(EV.mix(drows[nread:], [1.0] * (len(drows) - nread)))
            print(f"  {'READER FAMILY (12)':<24} diff {sr[0]:+7.3f} +-{sr[1]:.3f}    OTHERS (13) diff {si[0]:+7.3f} +-{si[1]:.3f}")
        for o in h2h:
            if o == b:
                continue
            s = EV.stats(EV.row_of(pairs(b, o)))
            print(f"  H2H vs {Path(o).stem:<17} {s[0]:+7.3f} +-{s[1]:.3f}")
        slow = 0.0
        notes = {}
        for o in opps:
            for s in a.seeds:
                r = json.loads((CACHE / key(b, o, s, a.deals)).read_text())
                slow = max(slow, r["slowest"]["ms"])
                for k, v in r["notes"][0].items():
                    notes[k] = notes.get(k, 0) + v
        print(f"  slowest call {slow:.2f} ms; notes {notes or 'none'}")


if __name__ == "__main__":
    main()
