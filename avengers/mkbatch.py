"""avengers/mkbatch.py - build avengers/cand/bNN_name.py from avengers/captain_america.py + named patch."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "captain_america.py")
OUT = os.path.join(HERE, "cand")

PATCHES = {
    "b01_thsig15": [("SIG_R = 1.0", "SIG_R = 1.5")],
    "b02_thw64": [("TH_PRIOR = ((2.0, 0.75), (7.0, 0.25))", "TH_PRIOR = ((2.0, 0.6), (7.0, 0.4))")],
    "b04_nplan8": [("NPLAN = 6", "NPLAN = 8")],
    "b05_respm05": [("RISK = 60.0       # utility curvature",
                     "RISK = 60.0       # utility curvature\nRESP_M = 0.5      # extra edge per lot wanted when I answer"),
                    ("                if qty > 0:\n                    x = qty * (V - price - 2)\n                elif qty < 0:\n                    x = -qty * (price - 2 - V)\n                else:\n                    x = 0.0",
                     "                if qty > 0:\n                    x = qty * (V - price - 2 - RESP_M)\n                elif qty < 0:\n                    x = -qty * (price - 2 - V - RESP_M)\n                else:\n                    x = 0.0")],
    "b06_roll25": [("                if V - q - 2 > 0:\n                    n = min(2, 10 - pos)\n                    pos += n\n                    Q += n\n                    pnl += n * (V - q - 2)\n                elif q - 2 - V > 0:",
                    "                if V - q - 2.5 > 0:\n                    n = min(2, 10 - pos)\n                    pos += n\n                    Q += n\n                    pnl += n * (V - q - 2.5)\n                elif q - 2.5 - V > 0:")],
    "b10_probe070": [("P_EXT = 0.9", "P_EXT = 0.8"), ("P_PROBE = 0.85", "P_PROBE = 0.70")],
    "b11_delta10": [("DELTAS = (2.0, 2.5, 3.0, 3.5, 4.5, 6.0)",
                     "DELTAS = (2.0, 2.5, 3.0, 3.5, 4.5, 6.0, 8.0, 10.0)"),
                    ("        cands = [bp, f0[0], f0[0] + 3.05, f0[0] - 3.05]\n        if len(f0) > 1:\n            cands += [f0[1] + 6.05, f0[1] - 6.05]",
                     "        cands = [bp, f0[0], f0[0] + 3.05, f0[0] - 3.05, f0[0] + 7.05, f0[0] - 7.05]\n        if len(f0) > 1:\n            cands += [f0[1] + 6.05, f0[1] - 6.05]")],
}


def main():
    src = open(SRC).read()
    for name, reps in PATCHES.items():
        s = src
        for old, new in reps:
            if old not in s:
                print(f"{name}: MISSING {old[:70]!r}")
                break
            s = s.replace(old, new, 1)
        else:
            s = s.replace("# Version: captain_america (v01), parent moscow, idea:",
                          f"# Version: cand {name}, parent captain_america, idea:", 1)
            fn = os.path.join(OUT, name + ".py")
            open(fn, "w").write(s)
            print("wrote", fn)


if __name__ == "__main__":
    main()
