"""avengers/mkcand.py - build avengers/cand/aNN_name.py from heist/moscow.py + a named patch.

Patches (each is a (old, new) replacement pair on moscow source):
  a01_j1public : my first quote of the deal is the public estimate for BOTH seats (j==0 or j==1)
  a02_delta812 : DELTAS += (8.0, 12.0)
  a03_carry065 : CARRY 0.82 -> 0.65
  a03_carry10  : CARRY 0.82 -> 1.0
  a04_naive045 : P_NAIVE 0.6 -> 0.45
  a05_blend018 : P_BLEND 0.12 -> 0.18
  a07_swpth3   : SWAP_TH round5 4.0 -> 3.0
  a08_probe075 : P_PROBE 0.85 -> 0.75
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "heist", "moscow.py")
OUT = os.path.join(HERE, "cand")

PATCHES = {
    "a01_j1public": [(
        "        if j == 0:\n            return self._public(obs)\n",
        "        if j in (0, 1):\n            return self._public(obs)\n")],
    "a02_delta812": [(
        "DELTAS = (2.0, 2.5, 3.0, 3.5, 4.5, 6.0)",
        "DELTAS = (2.0, 2.5, 3.0, 3.5, 4.5, 6.0, 8.0, 12.0)")],
    "a03_carry065": [("CARRY = 0.82", "CARRY = 0.65")],
    "a03_carry10": [("CARRY = 0.82", "CARRY = 1.0")],
    "a04_naive045": [("P_NAIVE = 0.6", "P_NAIVE = 0.45")],
    "a05_blend018": [("P_BLEND = 0.12", "P_BLEND = 0.18")],
    "a07_swpth3": [("SWAP_TH = (15.0, 12.0, 9.0, 6.0, 4.0)", "SWAP_TH = (15.0, 12.0, 9.0, 6.0, 3.0)")],
    "a08_probe075": [("P_PROBE = 0.85", "P_PROBE = 0.75")],
}


def main():
    src = open(SRC).read()
    for name, reps in PATCHES.items():
        s = src
        for old, new in reps:
            if old not in s:
                print(f"{name}: PATCH MISSING ({old!r})")
                break
            s = s.replace(old, new, 1)
        else:
            # version line
            s = s.replace(
                "# Version: moscow (v05), parent denver, idea:",
                f"# Version: cand {name}, parent moscow, idea:", 1)
            fn = os.path.join(OUT, name + ".py")
            open(fn, "w").write(s)
            print(f"{name}: wrote {fn}")


if __name__ == "__main__":
    main()
