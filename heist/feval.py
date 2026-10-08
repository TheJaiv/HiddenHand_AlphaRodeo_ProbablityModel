"""heist/feval.py - score matrix: several bots x several opponents x seeds, in parallel, cached.

    python3 heist/feval.py --bots A.py B.py --vs X.py Y.py --deals 400 --seeds 1 2 [--procs 8]

Same game and seeding as tools/eval.py (shared `random` seeded per game). Results are cached in
heist/data/feval_cache.json keyed by (file content hash of bot, of opponent, seed, deals), so a
re-run only plays what changed. Prints score (and +-2se) per bot and opponent, and per-pair lists
are kept for paired differences (see pairs()).
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import random
import statistics
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
sys.path.insert(0, KIT)

from bot_loader import load_for_testing        # noqa: E402
from engine import derive_seed, play_match     # noqa: E402

CACHE = os.path.join(HERE, "data", "feval_cache.json")
_classes: dict = {}


def fhash(path: str) -> str:
    return hashlib.sha1(open(path, "rb").read()).hexdigest()[:12]


def cls(path: str):
    if path not in _classes:
        _classes[path] = load_for_testing(path, quiet=True)
    return _classes[path]


def run(job):
    bot, opp, seed, deals = job
    b, o = cls(bot), cls(opp)
    game = itertools.count()

    def make_bot():
        random.seed(derive_seed(seed, "rng", next(game)))
        return b()

    r = play_match(make_bot, o, n_deals=deals, seed=seed)
    pd = r["per_deal"]
    pairs = [x + y for x, y in zip(pd[::2], pd[1::2])]
    return [round(p, 3) for p in pairs]


def ss(p: float) -> float:
    return math.copysign(math.sqrt(abs(p)), p)


def load_cache() -> dict:
    try:
        return json.load(open(CACHE))
    except Exception:
        return {}


def matrix(bots, opps, seeds, deals, procs=8, verbose=True) -> dict:
    """{(bot, opp): [pair pnl over all seeds]} with caching."""
    cache = load_cache()
    keys = {}
    jobs = []
    for b in bots:
        for o in opps:
            for s in seeds:
                k = f"{fhash(b)}|{fhash(o)}|{s}|{deals}"
                keys[(b, o, s)] = k
                if k not in cache:
                    jobs.append((b, o, s, deals))
    if jobs:
        if verbose:
            print(f"  playing {len(jobs)} matches ({deals} deals) on {procs} processes...", flush=True)
        with Pool(min(procs, len(jobs))) as pool:
            res = pool.map(run, jobs, chunksize=1)
        cache = load_cache()
        for j, r in zip(jobs, res):
            cache[keys[j[:3]]] = r
        tmp = CACHE + ".tmp"
        json.dump(cache, open(tmp, "w"))
        os.replace(tmp, CACHE)
    return {(b, o): [p for s in seeds for p in cache[keys[(b, o, s)]]] for b in bots for o in opps}


def score(pairs) -> tuple:
    v = [ss(p) for p in pairs]
    return statistics.mean(v), 2 * statistics.stdev(v) / math.sqrt(len(v))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bots", nargs="+", required=True)
    ap.add_argument("--vs", nargs="+", required=True)
    ap.add_argument("--deals", type=int, default=400)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1])
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    bots = [os.path.abspath(x) for x in a.bots]
    opps = [os.path.abspath(x if os.path.exists(x) else os.path.join(KIT, "strategies", x + ".py")) for x in a.vs]
    M = matrix(bots, opps, a.seeds, a.deals, a.procs)
    name = lambda p: os.path.basename(p)[:-3]
    print(f"{'opponent':<28}" + "".join(f"{name(b)[:14]:>16}" for b in bots))
    for o in opps:
        print(f"{name(o):<28}" + "".join(f"{score(M[(b, o)])[0]:+9.2f} {score(M[(b, o)])[1]:5.2f} " for b in bots))
    return 0


if __name__ == "__main__":
    sys.exit(main())
