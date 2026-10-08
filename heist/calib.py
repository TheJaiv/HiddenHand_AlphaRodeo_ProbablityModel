"""heist/calib.py - calibration of the field model: local score of our files vs each imitation,
next to the live score of the same file against that team's newest entry.

    python3 heist/calib.py [--deals 400] [--seeds 1 2] [--teams ...]

Our files with a live record (entry -> file) are listed in KNOWN. A team is calibrated when every
known file's local score is within 1.5 of its live score.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import feval   # noqa: E402

KNOWN = {          # our live entry -> the file that plays exactly like it
    "486": "heist/tokyo.py", "452": "heist/tokyo.py",
    "466": "heist/berlin.py", "459": "heist/berlin.py",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deals", type=int, default=400)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2])
    ap.add_argument("--teams", nargs="+")
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    m = json.load(open(os.path.join(HERE, "data", "matrix.json"), encoding="utf-8"))
    fits = json.load(open(os.path.join(HERE, "data", "fits.json"), encoding="utf-8"))
    teams = a.teams or sorted(fits)
    rows = []
    jobs_bots = sorted(set(KNOWN.values()))
    opps = []
    for t in teams:
        if t not in fits:
            continue
        key = f"{t}#{fits[t]['entry']}"
        live = {e: m["ours"][e][key] for e in KNOWN if e in m["ours"] and key in m["ours"][e]}
        if not live:
            continue
        opps.append(os.path.join(KIT, fits[t]["file"]))
        rows.append((t, key, live))
    bots = [os.path.join(KIT, b) for b in jobs_bots]
    M = feval.matrix(bots, opps, a.seeds, a.deals, a.procs)
    out = {}
    print(f"{'team':<24}{'file':<10}{'live':>8}{'local':>8}{'diff':>7}")
    for (t, key, live), o in zip(rows, opps):
        ok = True
        for e, sc in sorted(live.items()):
            b = os.path.join(KIT, KNOWN[e])
            loc = feval.score(M[(b, o)])[0]
            d = loc - sc
            ok &= abs(d) <= 1.5
            print(f"{t[:23]:<24}{os.path.basename(KNOWN[e])[:-3] + '#' + e:<10}{sc:+8.2f}{loc:+8.2f}{d:+7.2f}")
            out.setdefault(t, []).append({"entry": e, "live": sc, "local": loc})
        print(f"{'':<24}{'CALIBRATED' if ok else 'not calibrated'}")
    json.dump(out, open(os.path.join(HERE, "data", "calib.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
