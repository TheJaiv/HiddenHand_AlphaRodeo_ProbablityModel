"""Verify a fitted team at 500 deals x seeds 1 2 and write zoo/arena_cal_<team>.py (or an attempt file).

    python finalize.py KEY PARAMS.json
"""
import json, os, sys
import build, cal, jfit

NAMES = {"tp": "teenpatti", "qt": "quants_treasure", "cy": "cyberpsycho", "ph": "paperhands",
         "gz": "genz7", "aj": "aj_the_trader"}
LIVE_ID = {"r1": "#351 rival_1", "r2": "#368 rival_2", "h1": "#383 hunt_v01", "h2": "#393 hunt_v02",
           "naive": "House naive", "reader": "House reader", "sharp": "House sharp"}
DESC = {}


def main():
    key, pfile = sys.argv[1], sys.argv[2]
    params = json.load(open(pfile))
    c = jfit.TEAMS[key]
    tmp = f"cand/{key}_final.py"
    build.write(tmp, "tmp", params)
    t = cal.run([tmp], tuple(c["tgt"]), deals=500, seeds=(1, 2))[os.path.abspath(tmp)]
    rows, ok = [], True
    for o, live in c["tgt"].items():
        m, e = t[o]                     # from the side of OUR bot (r1/r2/h1/h2) or of the house bot
        d = m - live
        crit = o in ("r1", "r2", "h1")
        passed = abs(d) <= 1.5
        if crit and not passed:
            ok = False
        rows.append((o, live, m, e, d, passed, crit, "our side" if o[0] in "rh" and o != "reader" else "house side"))
    tape = jfit.tape_loss(key, params)
    print(key, "tape loss", round(tape, 3))
    for r in rows:
        print(f"  {r[0]:7s} {LIVE_ID[r[0]]:14s} live {r[1]:+6.2f} local {r[2]:+6.2f} (+-{r[3]:.2f}) diff {r[4]:+5.2f} "
              f"{'PASS' if r[5] else 'FAIL'}{'' if r[6] else ' (extra)'}  [{r[7]}]")
    json.dump({"rows": rows, "params": params, "tape": tape, "ok": ok}, open(f"final_{key}.json", "w"))


if __name__ == "__main__":
    main()
