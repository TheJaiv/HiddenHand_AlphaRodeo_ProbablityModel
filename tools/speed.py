"""
tools/speed.py - how long a bot's calls really take (local only)
================================================================

eval.py times calls while every core is busy, so one stalled call can look
like 90 ms. This plays deals in ONE quiet process and reports the spread:

    python tools/speed.py BOT                     vs sharp, rival_1..3, hider; 60 deals each
    python tools/speed.py BOT --deals 200 --vs reader zoo/old_plan.py

The arena limit is 50 ms per call, and the arena machine may be slower than
this laptop, so aim for a max well under 10 ms.
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
import time
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT))

from backtester import resolve                 # noqa: E402  (kit files, used as they are)
from bot_loader import load_for_testing        # noqa: E402
from engine import derive_seed, play_deal      # noqa: E402

DEFAULT_VS = ["sharp", "zoo/rival_1.py", "zoo/rival_2.py", "zoo/rival_3.py", "zoo/hider.py"]


class Timed:
    """Wraps a bot; records how long every move/quote/respond call takes."""

    def __init__(self, bot, times: dict):
        self.bot, self.times = bot, times

    def _call(self, method, *args):
        t0 = time.perf_counter()
        try:
            return getattr(self.bot, method)(*args)
        finally:
            self.times[method].append((time.perf_counter() - t0) * 1000)

    def move(self, obs):
        return self._call("move", obs)

    def quote(self, obs):
        return self._call("quote", obs)

    def respond(self, obs, price):
        return self._call("respond", obs, price)


def main() -> int:
    ap = argparse.ArgumentParser(description="Hidden Hand: per-call timing in one quiet process")
    ap.add_argument("bot")
    ap.add_argument("--vs", nargs="+", default=DEFAULT_VS, metavar="BOT")
    ap.add_argument("--deals", type=int, default=60, help="deals per opponent (each played both ways)")
    args = ap.parse_args()

    bot_cls = load_for_testing(str(resolve(args.bot)), quiet=True)
    times = {"move": [], "quote": [], "respond": []}
    for name in args.vs:
        opp_cls = load_for_testing(str(resolve(name)), quiet=True)
        for d in range(args.deals):
            seed = derive_seed(7, d)
            for k, seats in enumerate(((True, False), (False, True))):   # both seatings
                random.seed(derive_seed(7, "rng", 2 * d + k))
                me, opp = Timed(bot_cls(), times), opp_cls()
                play_deal(*((me, opp) if seats[0] else (opp, me)), seed)

    print(f"{Path(args.bot).stem}: {args.deals} deals x {len(args.vs)} opponents, both seatings, one process")
    print(f"  {'call':<8}{'calls':>7}{'median':>9}{'p99':>9}{'max':>9}   (ms)")
    for method, ts in times.items():
        if ts:
            ts.sort()
            print(f"  {method:<8}{len(ts):>7}{statistics.median(ts):>9.2f}"
                  f"{ts[int(len(ts) * 0.99)]:>9.2f}{ts[-1]:>9.2f}")
    worst = max(max(ts) for ts in times.values() if ts)
    print(f"  slowest call {worst:.2f} ms: " + ("fine (well under 10 ms)" if worst < 10 else
                                               "too close to the 50 ms limit, speed it up"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
