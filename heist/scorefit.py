"""heist/scorefit.py - fit a team's imitation to OUR LIVE SCORES against it (plus its replays).

    python3 heist/scorefit.py "Genz7" [--cands 40] [--deals 200]

Starts from the replay fit in data/fits.json, perturbs the parameters that replays cannot pin down
(take thresholds, follow weight / step, reading, trade learning, swap accounting, hiding), and scores each
candidate by the squared error between local and live scores of every file of ours that played that entry,
plus the replay loss. The best candidate is written to heist/opp/sf_<team>.py and data/scorefits.json.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics as S
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import feval        # noqa: E402
import fit_opp      # noqa: E402
import build_field  # noqa: E402

KNOWN = {"486": "heist/tokyo.py", "452": "heist/tokyo.py", "466": "heist/berlin.py", "459": "heist/berlin.py",
         "495": "heist/nairobi.py", "505": "heist/rio.py", "513": "heist/moscow.py", "561": "heist/cand/c23_thfix.py",
         "565": "heist/lisbon.py", "569": "heist/test_j01_safeq.py", "573": "heist/test_e01_thonly.py",
         "586": "heist/stockholm.py", "588": "heist/test_u01_nudge30.py"}
KNOBS = {"TH": (0.0, 8.0), "TH2": (0.0, 9.0), "W": (0.0, 1.0), "C": (-3.5, 3.5), "T": (0.0, 1.0), "TL": (-1.0, 3.0),
         "SA": (0.0, 1.2), "HIDE": (-0.5, 1.0), "TR": (0.0, 1.2), "ASYM": (-6.0, 6.0), "SKEW": (-0.5, 1.5)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("team")
    ap.add_argument("--cands", type=int, default=40)
    ap.add_argument("--deals", type=int, default=200)
    ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    m = json.load(open(os.path.join(HERE, "data", "matrix.json")))
    fits = json.load(open(os.path.join(HERE, "data", "fits.json")))
    team = a.team
    e = fits[team]["entry"]
    key = f"{team}#{e}"
    live = {f: m["ours"][en][key] for en, f in KNOWN.items() if en in m["ours"] and key in m["ours"][en]}
    if len(live) < 2:
        sys.exit(f"{key}: only {len(live)} live points")
    plays = fit_opp.load(team, e)
    P0 = dict(fits[team]["P"])
    rng = random.Random(a.seed)
    cands = [P0]
    for i in range(a.cands - 1):
        P = dict(P0)
        for k in rng.sample(list(KNOBS), 4):
            lo, hi = KNOBS[k]
            P[k] = min(hi, max(lo, P.get(k, 0.0) + rng.gauss(0, 0.35 * (hi - lo))))
        if P.get("TH2", 0) < P.get("TH", 0):
            P["TH2"] = P["TH"]
        cands.append(P)
    tmpd = os.path.join(HERE, "opp", "tmp")
    os.makedirs(tmpd, exist_ok=True)
    files = []
    for i, P in enumerate(cands):
        st = fit_opp.evaluate(P, plays, detail=True)
        fn = build_field.write(f"{team} sf{i}", e, P, st)
        dst = os.path.join(tmpd, os.path.basename(fn))
        os.replace(fn, dst)
        files.append((P, st[0], dst))
    bots = [os.path.join(KIT, f) for f in live]
    M = feval.matrix(bots, [f for _, _, f in files], [a.seed], a.deals, 9, verbose=True)
    rows = []
    for P, rl, f in files:
        err = [feval.score(M[(os.path.join(KIT, b), f)])[0] - live[b] for b in live]
        mse = S.mean(x * x for x in err)
        bias = S.mean(err)
        rows.append((mse + 0.5 * rl, mse, bias, rl, P, f, err))
    rows.sort(key=lambda r: r[0])
    base = [r for r in rows if r[5] == files[0][2]][0]
    print(f"{key}: {len(live)} live points; replay fit: mse {base[1]:.2f} bias {base[2]:+.2f} replay loss {base[3]:.2f}")
    for obj, mse, bias, rl, P, f, err in rows[:3]:
        print(f"  best: mse {mse:.2f} (rmse {mse ** 0.5:.2f}) bias {bias:+.2f} replay loss {rl:.2f}   "
              + " ".join(f"{k}={P[k]:.2f}" for k in KNOBS if k in P))
    best = rows[0]
    st = fit_opp.evaluate(best[4], plays, detail=True)
    fn = build_field.write(f"{team} sf", e, best[4], st)
    out = os.path.join(HERE, "opp", f"sf_{build_field.slug(team)}.py")
    os.replace(fn, out)
    sf_fn = os.path.join(HERE, "data", "scorefits.json")
    sf = json.load(open(sf_fn)) if os.path.exists(sf_fn) else {}
    sf[team] = {"entry": e, "P": best[4], "rmse": best[1] ** 0.5, "bias": best[2], "replay_loss": best[3],
                "file": os.path.relpath(out, KIT), "points": len(live)}
    json.dump(sf, open(sf_fn, "w"), indent=1)
    print("wrote", os.path.relpath(out, KIT))


if __name__ == "__main__":
    main()
