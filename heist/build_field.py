"""heist/build_field.py - fit an imitation of every team's newest entry and write heist/opp/opp_<team>.py.

    python3 -I heist/build_field.py [--iters 1500] [--teams "A" "B" ...]

Each file is self-contained (opp_core source + the fitted P). Writes heist/data/fits.json with the
replay agreement of every fit.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fit_opp   # noqa: E402

OUTD = os.path.join(HERE, "opp")
CORE = open(os.path.join(HERE, "opp_core.py"), encoding="utf-8").read()


def slug(team):
    return re.sub(r"[^a-z0-9]+", "_", team.lower()).strip("_")


def write(team, entry, P, stats):
    os.makedirs(OUTD, exist_ok=True)
    body = CORE.split('"""', 2)[2]          # drop the core's docstring
    src = (f"# Team Name: Field model - {team}\n# Members: none (local imitation, never uploaded)\n# Mentor: none\n"
           f'"""opp_{slug(team)}.py - imitation of live team {team} #{entry}, fitted to its public replays\n'
           f"(heist/fit_opp.py): quote err {stats[1]:.2f}, respond miss {stats[2]:.2f}, move miss {stats[3]:.2f}."
           f'\nSee heist/opp_core.py for what the parameters mean."""\n'
           + body + f"\n\nBot = make_bot({json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in P.items()})})\n")
    fn = os.path.join(OUTD, f"opp_{slug(team)}.py")
    open(fn, "w", encoding="utf-8").write(src)
    return fn


def main():
    args = sys.argv[1:]
    iters = int(args[args.index("--iters") + 1]) if "--iters" in args else 1500
    m = json.load(open(os.path.join(HERE, "data", "matrix.json"), encoding="utf-8"))
    teams = args[args.index("--teams") + 1:] if "--teams" in args else [
        t for t in m["newest"] if t != "Alpha Rodeo" and not t.startswith("House")]
    fits_fn = os.path.join(HERE, "data", "fits.json")
    fits = json.load(open(fits_fn)) if os.path.exists(fits_fn) else {}
    for team in teams:
        e = m["newest"][team]
        best, plays = fit_opp.fit(team, e, iters=iters, verbose=False)
        if not plays:
            print(f"{team} #{e}: no replays cached")
            continue
        P = best[0][1]
        st = fit_opp.evaluate(P, plays, detail=True)
        fn = write(team, e, P, st)
        fits[team] = {"entry": e, "plays": len(plays), "loss": st[0], "qerr": st[1], "rmiss": st[2],
                      "mmiss": st[3], "P": P, "file": os.path.relpath(fn, os.path.dirname(HERE))}
        json.dump(fits, open(fits_fn, "w"), indent=1)
        print(f"{team:<22} #{e:<4} plays {len(plays):3d}  quote err {st[1]:.2f}  respond miss {st[2]:.2f}  "
              f"move miss {st[3]:.2f}  W {P['W']:.2f} C {P['C']:+.2f} T {P['T']:.2f} TH {P['TH']:.1f}", flush=True)


if __name__ == "__main__":
    main()
