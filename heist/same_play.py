"""heist/same_play.py - do two bot files play IDENTICALLY (every quote, answer, move) on many deals?

    python3 heist/same_play.py A.py B.py [--deals 100]
Also reports per-call wall time of both (median / p99 / max), measured in the same process.
"""
import argparse
import os
import sys
import time

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)
from bot_loader import load_for_testing   # noqa: E402
from engine import derive_seed, play_deal  # noqa: E402

OPPS = ["heist/opp/opp_thunderx.py", "heist/opp/opp_godtier.py", "heist/opp/opp_paperhands.py",
        "heist/opp/opp_iitbhuavengers.py", "heist/opp/opp_quant_qods.py", "heist/opp/opp_happy_happy_463.py"]


class T:
    def __init__(self, b, ts):
        self.b, self.ts = b, ts

    def _c(self, m, *a):
        t0 = time.perf_counter()
        r = getattr(self.b, m)(*a)
        self.ts.append((time.perf_counter() - t0) * 1000)
        return r

    def move(self, o):
        return self._c("move", o)

    def quote(self, o):
        return self._c("quote", o)

    def respond(self, o, p):
        return self._c("respond", o, p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--deals", type=int, default=100)
    a = ap.parse_args()
    A = load_for_testing(a.a, quiet=True)
    B = load_for_testing(a.b, quiet=True)
    ta, tb = [], []
    diff = n = 0
    for f in OPPS:
        O = load_for_testing(os.path.join(KIT, f), quiet=True)
        for d in range(a.deals):
            sd = derive_seed(77, d)
            for seat in (0, 1):
                ra = play_deal(*((T(A(), ta), O()) if seat == 0 else (O(), T(A(), ta))), sd)
                rb = play_deal(*((T(B(), tb), O()) if seat == 0 else (O(), T(B(), tb))), sd)
                n += 1
                if ra["log"]["rounds"] != rb["log"]["rounds"] or ra["pnl"] != rb["pnl"]:
                    diff += 1
    for name, ts in ((os.path.basename(a.a), ta), (os.path.basename(a.b), tb)):
        ts.sort()
        print(f"{name:<22} calls {len(ts)}  median {ts[len(ts)//2]:.3f}  p99 {ts[int(len(ts)*.99)]:.3f}  max {ts[-1]:.3f} ms  total {sum(ts)/1000:.2f} s")
    print(f"{n} plays: {diff} differ" + ("  -> IDENTICAL PLAY" if diff == 0 else ""))


if __name__ == "__main__":
    main()
