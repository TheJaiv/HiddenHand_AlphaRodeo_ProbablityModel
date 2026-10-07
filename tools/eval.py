"""
tools/eval.py - score one bot against a whole pool of opponents (local only)
=============================================================================

Never uploaded. It does not change the kit: it calls engine.play_match, the
same game backtester.py plays, once per (opponent, seed), in parallel.

    python tools/eval.py BOT                         vs the default pool, seeds 1 2 3
    python tools/eval.py BOT --vs naive zoo/x.py     vs only these opponents
    python tools/eval.py BOT --deals 500 --seeds 1   quicker, noisier
    python tools/eval.py BOT --compare OLD_BOT       OLD_BOT plays the same deals; print BOT - OLD
    python tools/eval.py BOT --worst 3               replay the 3 deal pairs BOT lost most, per opponent

A bot is a path, or a house bot name (naive, reader, sharp), as in backtester.py.

Default pool: strategies/naive.py, reader.py, sharp.py and every zoo/*.py,
minus BOT itself (a bot mirrored against itself always scores exactly 0).

zoo/weights.json sets the WEIGHTED line, keyed by file name without .py,
or by a pattern such as "rival_*" (fnmatch rules). An exact name wins over a
pattern; otherwise the first matching pattern in the file is used:
    {"champ_v1": 2.0, "naive": 0.5, "rival_*": 2.0}
Any opponent nothing matches has weight 1.0.

Statistics. Every deal is played twice with the hands swapped, and the pair
(the two PnLs added) is the unit of noise, exactly as in backtester.py:
    score     mean over pairs p of sign(p) * sqrt(|p|)    (what the arena ranks)
    PnL/deal  mean over pairs p of p / 2
    +-2se     2 standard errors of that mean

Randomness. Before every deal, Python's shared `random` module is seeded from
(seed, deal, seating). A bot that calls random.random() etc. therefore gets the
same numbers on every run, BOT and OLD get the same numbers in --compare, and
--worst replays the exact deal. (A bot that makes its own unseeded
random.Random() is still not repeatable.)
"""

from __future__ import annotations

import argparse
import fnmatch
import itertools
import json
import math
import os
import random
import statistics
import sys
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent      # the folder holding engine.py
sys.path.insert(0, str(KIT))

from backtester import describe, resolve                # noqa: E402  (kit files, used as they are)
from bot_loader import check_source, load_for_testing   # noqa: E402
from engine import derive_seed, play_deal, play_match   # noqa: E402

HOUSE = ("naive", "reader", "sharp")


def stem(path: str) -> str:
    """'/.../zoo/champ_v1.py' -> 'champ_v1'"""
    return Path(path).stem


def weight_of(name: str, weights: dict) -> float:
    """An exact key first, then the first pattern key ("rival_*") that matches."""
    if name in weights:
        return float(weights[name])
    for pattern, x in weights.items():
        if fnmatch.fnmatchcase(name, pattern):
            return float(x)
    return 1.0


# ── Timing ──────────────────────────────────────────────────────────

class Timed:
    """Wraps a bot and records its slowest single move/quote/respond call."""

    def __init__(self, bot, slowest: dict):
        self.bot = bot
        self.slowest = slowest          # shared by every deal of one match

    def _call(self, method, *args):
        t0 = time.perf_counter()
        try:
            return getattr(self.bot, method)(*args)
        finally:                        # time crashes too
            ms = (time.perf_counter() - t0) * 1000
            if ms > self.slowest["ms"]:
                self.slowest.update(ms=ms, method=method)

    def move(self, obs):
        return self._call("move", obs)

    def quote(self, obs):
        return self._call("quote", obs)

    def respond(self, obs, price):
        return self._call("respond", obs, price)

    def __getattr__(self, name):
        # Anything else the engine asks for (e.g. last_call_ms) comes from the real bot.
        return getattr(self.bot, name)


# ── One match, run inside a worker process ──────────────────────────

_classes: dict[str, type] = {}          # path -> Bot class, loaded once per process


def bot_class(path: str) -> type:
    if path not in _classes:
        _classes[path] = load_for_testing(path, quiet=True)
    return _classes[path]


def seed_random(seed: int, k: int) -> None:
    """Seed the shared `random` module for game number k of a match.

    play_match plays deal d twice, normal then swapped, so its games are
    k = 2d and k = 2d + 1. show_worst uses the same numbering for its replays.
    """
    random.seed(derive_seed(seed, "rng", k))


def run_match(job: tuple) -> dict:
    """bot vs opp on one seed. Only plain data goes back to the main process."""
    bot, opp, seed, deals = job
    bot_cls, opp_cls = bot_class(bot), bot_class(opp)
    slowest = {"ms": 0.0, "method": "-"}
    game = itertools.count()                # 0, 1, 2, ...: one per game play_match plays

    def make_bot():
        # play_match builds BOT first, then the opponent, before each game,
        # so seeding here fixes every random number both bots draw in that game.
        seed_random(seed, next(game))
        return Timed(bot_cls(), slowest)

    r = play_match(make_bot, opp_cls, n_deals=deals, seed=seed)
    return {"per_deal": r["per_deal"], "notes": r["notes"], "slowest": slowest}


# ── Statistics ──────────────────────────────────────────────────────
# A "row" is two lists with one number per deal pair: (score parts, PnL-per-deal
# parts). Keeping the per-pair numbers, not just their means, lets us average
# opponents pair by pair: every opponent plays the SAME deals (same seeds), so
# their luck is shared, and the standard error has to see that.

def pairs_of(per_deal: list) -> list:
    """Mirrored deals come in twos (same cards, seats swapped): add each two."""
    return [a + b for a, b in zip(per_deal[::2], per_deal[1::2])]


def ssqrt(p: float) -> float:
    """Signed square root: 100 -> 10, -16 -> -4."""
    return math.copysign(math.sqrt(abs(p)), p)


def row_of(pairs: list) -> tuple:
    return [ssqrt(p) for p in pairs], [p / 2 for p in pairs]


def diff_row(new_pairs: list, old_pairs: list) -> tuple:
    """Pair by pair BOT - OLD. Same deals, so most of the luck cancels."""
    return ([ssqrt(n) - ssqrt(o) for n, o in zip(new_pairs, old_pairs)],
            [(n - o) / 2 for n, o in zip(new_pairs, old_pairs)])


def mix(rows: list, weights: list) -> tuple:
    """Weighted average of several opponents' rows, one deal pair at a time."""
    W = sum(weights)
    return tuple([sum(w * r[k][i] for w, r in zip(weights, rows)) / W
                  for i in range(len(rows[0][k]))] for k in (0, 1))


def mean_2se(values: list) -> tuple:
    se = statistics.stdev(values) / len(values) ** 0.5 if len(values) > 1 else float("nan")
    return statistics.mean(values), 2 * se


def stats(row: tuple) -> tuple:
    """(score, +-2se, PnL per deal, +-2se). The PnL part equals backtester.py's
    mean(per_deal) and 2 * stdev(pairs) / 2 / sqrt(pairs)."""
    return (*mean_2se(row[0]), *mean_2se(row[1]))


# ── Printing ────────────────────────────────────────────────────────

def print_row(name: str, label, s: tuple) -> None:
    print(f"  {name:<18}{str(label):>5}  {s[0]:+8.3f} {s[1]:6.3f}   {s[2]:+8.2f} {s[3]:6.2f}")


def print_compare_row(name: str, new: tuple, old: tuple, d: tuple) -> None:
    print(f"  {name:<18}{new[0]:+8.3f}{old[0]:+8.3f}{d[0]:+8.3f} {d[1]:6.3f}"
          f"   {new[2]:+8.2f}{old[2]:+8.2f}{d[2]:+8.2f} {d[3]:6.2f}")


def show_worst(bot: str, opps: list, seeds: list, results: dict, n: int) -> None:
    """Replay the n deal pairs BOT lost most against each opponent.

    play_match only keeps the first deal's replay, so each bad deal is played
    again with engine.play_deal on the same seed play_match used for it.
    """
    for opp in opps:
        names = (stem(bot), stem(opp) if stem(opp) != stem(bot) else stem(opp) + "2")
        bad = sorted((p, seed, d) for seed in seeds
                     for d, p in enumerate(pairs_of(results[bot, opp, seed]["per_deal"])))
        print(f"\n=== {names[0]} vs {names[1]}: the {n} deal pairs {names[0]} lost most ===")
        for p, seed, d in bad[:n]:
            s = derive_seed(seed, d)                      # how play_match seeds deal d
            a, b = bot_class(bot), bot_class(opp)
            seed_random(seed, 2 * d)                                  # same random numbers as in the match
            first = play_deal(a(), b(), s, names=names)               # BOT in seat 0
            seed_random(seed, 2 * d + 1)
            second = play_deal(b(), a(), s, names=names[::-1])        # hands swapped
            again = first["pnl"][0] + second["pnl"][1]
            print(f"\n--- seed {seed}, deal {d}: {names[0]} pair PnL {p:+.1f}")
            if abs(again - p) > 1e-6:
                print(f"  (replay gave {again:+.1f}: a bot uses an unseeded random.Random(), "
                      f"so this is not the same deal)")
            print(describe(first["log"]) + "\n")
            print(describe(second["log"]))


# ── Main ────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Hidden Hand: one bot vs a pool of opponents")
    ap.add_argument("bot")
    ap.add_argument("--vs", nargs="+", metavar="BOT", help="opponents (default: house bots + zoo/*.py)")
    ap.add_argument("--deals", type=int, default=1000, help="deals per match, each played twice")
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--compare", metavar="OLD_BOT", help="run OLD_BOT on the same deals, print BOT - OLD")
    ap.add_argument("--worst", type=int, default=0, metavar="N",
                    help="per opponent, replay the N deal pairs BOT lost most")
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1),
                    help="worker processes (default: all cores but one). With every core busy, "
                         "the OS can stall a call past the engine's 50 ms limit, which then counts "
                         "as 'do nothing' and slightly changes results; use fewer for exact numbers")
    args = ap.parse_args()
    seeds = args.seeds

    # Every bot is kept as an absolute path string, so the same file always matches.
    bot = str(resolve(args.bot).resolve())
    old = str(resolve(args.compare).resolve()) if args.compare else None
    if old == bot:
        print(f"! --compare: BOT and OLD are the same file, so every diff is 0 by construction.\n"
              f"  To test the tool itself, copy the file and compare against the copy.")
    if args.vs:
        opps = [str(resolve(name).resolve()) for name in args.vs]
    else:
        opps = [str(KIT / "strategies" / f"{n}.py") for n in HOUSE]
        opps += [str(p) for p in sorted((KIT / "zoo").glob("*.py"))]
        if bot in opps:
            opps.remove(bot)
            print(f"(not playing {stem(bot)} against itself: that always scores 0)")

    # Load everything once here, so a broken file is reported before any work starts.
    bots = [bot] + ([old] if old and old != bot else [])   # same file: play it once
    for path in bots:
        try:
            bot_class(path)
        except Exception as e:
            sys.exit(f"cannot load {path}: {e}")
    for path in list(opps):
        try:
            bot_class(path)
        except Exception as e:
            print(f"! skipping opponent {stem(path)}, it does not load: {e}")
            opps.remove(path)
    if not opps:
        sys.exit("no opponents to play")
    verdict = check_source(bot)
    if not verdict.ok:
        print(f"! the arena would REJECT {stem(bot)}: " + "; ".join(verdict.errors))

    weights_file = KIT / "zoo" / "weights.json"
    weights = json.loads(weights_file.read_text()) if weights_file.exists() else {}
    w = [weight_of(stem(o), weights) for o in opps]

    # One job per (bot, opponent, seed); each job is one play_match call.
    jobs = [(b, o, seed, args.deals) for b in bots for o in opps for seed in seeds]
    procs = max(1, min(len(jobs), args.procs))
    print(f"{stem(bot)}: {len(opps)} opponents x seeds {' '.join(map(str, seeds))} x {args.deals} deals"
          f"  ({len(jobs)} matches on {procs} processes)", flush=True)
    t0 = time.time()
    with Pool(procs) as pool:
        results = {job[:3]: res for job, res in zip(jobs, pool.map(run_match, jobs))}
    print(f"done in {time.time() - t0:.1f} s")

    def pairs(b, o):
        """Every deal pair of b vs o, all seeds joined."""
        return [p for seed in seeds for p in pairs_of(results[b, o, seed]["per_deal"])]

    # ── BOT's table: per opponent and seed, then the mean over seeds ──
    print(f"\n  {'opponent':<18}{'seed':>5}  {'score':>8} {'+-2se':>6}   {'PnL/deal':>8} {'+-2se':>6}")
    rows = []
    for o in opps:
        for i, seed in enumerate(seeds):
            print_row(stem(o) if i == 0 else "", seed, stats(row_of(pairs_of(results[bot, o, seed]["per_deal"]))))
        rows.append(row_of(pairs(bot, o)))
        if len(seeds) > 1:
            print_row("", "mean", stats(rows[-1]))
    print()
    print_row("POOL AVERAGE", "", stats(mix(rows, [1.0] * len(rows))))
    print_row("WEIGHTED", "", stats(mix(rows, w)))
    listed = ", ".join(f"{stem(o)}={x:g}" for o, x in zip(opps, w) if x != 1.0)
    print(f"  (weights from zoo/weights.json: {listed or 'all 1.0'})" if weights_file.exists()
          else "  (no zoo/weights.json, so every weight is 1.0)")

    # ── --compare: OLD on the same deals, and BOT - OLD ──
    if old:
        print(f"\nCOMPARE {stem(bot)} (BOT) with {stem(old)} (OLD) on the same deals; diff = BOT - OLD")
        print(f"  {'opponent':<18}{'BOT':>8}{'OLD':>8}{'diff':>8} {'+-2se':>6}"
              f"   {'BOT':>8}{'OLD':>8}{'diff':>8} {'+-2se':>6}")
        print(f"  {'':<18}{'---------- score ----------':>31}   {'-------- PnL per deal -------':>31}")
        new_rows, old_rows, diff_rows = [], [], []
        for o in opps:
            new_rows.append(row_of(pairs(bot, o)))
            old_rows.append(row_of(pairs(old, o)))
            diff_rows.append(diff_row(pairs(bot, o), pairs(old, o)))
            print_compare_row(stem(o), stats(new_rows[-1]), stats(old_rows[-1]), stats(diff_rows[-1]))
        print()
        for label, ws in (("POOL AVERAGE", [1.0] * len(opps)), ("WEIGHTED", w)):
            print_compare_row(label, stats(mix(new_rows, ws)), stats(mix(old_rows, ws)),
                              stats(mix(diff_rows, ws)))

    # ── Speed: the slowest single call each bot made ──
    print()
    for b in bots:
        slow = max((r["slowest"] for k, r in results.items() if k[0] == b), key=lambda t: t["ms"])
        print(f"slowest call, {stem(b)}: {slow['ms']:.2f} ms in {slow['method']}()  "
              f"(arena limit 50 ms; timed under parallel load, so spikes happen: "
              f"use tools/speed.py for the real figure)")

    # ── Notes the engine kept: crashes, timeouts, unusable return values ──
    print("\nnotes (crashes, timeouts, bad return values):")
    found = False
    for b in bots:
        for o in opps:
            mine, theirs = Counter(), Counter()
            for seed in seeds:
                n_b, n_o = results[b, o, seed]["notes"]
                mine.update(n_b)
                theirs.update(n_o)
            for who, notes in ((stem(b), mine), (stem(o), theirs)):
                for msg, k in notes.items():
                    print(f"  ! {stem(b)} vs {stem(o)}: {who}: {msg}  (x{k})")
                    found = True
    if not found:
        print("  none")

    if args.worst > 0:
        show_worst(bot, opps, seeds, results, args.worst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
