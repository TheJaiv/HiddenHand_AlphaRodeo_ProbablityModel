"""Joint fit: replay agreement (teacher forcing) + live-score calibration.

    python jfit.py TEAM ITERS [DEALS]
"""
import json, os, random, sys, time
import tapes, build, oldp, cal
import cal_core

S = "/private/tmp/claude-501/-Users-jaiv-Library-Application-Support-Claude-scratch-workspaces-06f17f91-1d2c-486c-b604-12ba3a72a3e4-e5eb3a03-86c8-482f-b9a9-80062021399a-scratch-2026-10-07-7eeac4/4d555f3c-1164-4866-b8da-f57e9c90a1e8/scratchpad"
OURS_DIR = "../arena_cal_work/raw_ours"
TEAMS = {
    "tp": dict(dir="teenpatti", name="TeenPatti", entry=330, init="../arena_teenpatti_v4.py",
               tgt={"r1": -6.99, "r2": -2.56, "h1": -1.71, "h2": 1.13, "reader": -10.85}, fix={}),
    "qt": dict(dir=None, name="Quants Treasure", entry=377, init="../arena_quants_treasure.py",
               tgt={"r2": -4.28, "h1": -3.06, "h2": -2.78, "sharp": -15.29}, fix={"MIRROR": 1}),
    "cy": dict(dir="cyberpsycho", name="Cyberpsycho", entry=316, init=None,
               tgt={"r1": -1.63, "r2": -1.32, "h1": -1.64, "h2": -0.39}, fix={}),
    "ph": dict(dir="paperhands", name="PaperHands", entry=353, init="../arena_paperhands_v5.py",
               tgt={"r1": -3.03, "r2": -1.04, "h1": -0.62, "h2": 0.90, "naive": -9.51}, fix={"LIM_EXT": 1}),
    "gz": dict(dir="genz7", name="Genz7", entry=262, init="../arena_genz7.py",
               tgt={"r1": -2.66, "r2": -2.91, "h1": -0.31, "h2": 0.12, "reader": -12.84}, fix={}),
    "aj": dict(dir="aj_the_trader", name="AJ_The_Trader", entry=344, init="../arena_aj_the_trader.py",
               tgt={"r1": -2.88, "r2": -3.11, "h1": 2.61, "h2": 2.17, "naive": -9.77}, fix={}),
}
WT = {"r1": 1.0, "r2": 1.0, "h1": 1.0, "h2": 0.5, "reader": 0.3, "naive": 0.3, "sharp": 0.3}
SPACE = dict(T=(0, 1.5), W=(0, 1), SKEW_Q=(-2, 3), C_Q=(-3, 3), SKEW_R=(-1, 3), TH1=(0.5, 7), TH2=(0.5, 8),
             HIDE=(-1, 1), TRADE_EV=(-1, 3), TB_G=(-1, 2), TB_F=(0, 1), SANE_LO=(-10, 25), SANE_HI=(45, 90),
             SWAP_G=(0, 4))
CHOICE = dict(T_PRICE=[True, False], AVG_Q=[1, 2, 3], TB=[0, 1], SWAP_R=[2, 3, 4, 5])


def init_params(key):
    c = TEAMS[key]
    if c["init"]:
        p = oldp.oldparams(c["init"])
    else:
        lines = open(os.path.join(S, "combo3_cy.txt")).read().splitlines()
        best = [l for l in lines if l.startswith("BEST")]
        p = json.loads(best[-1][5:]) if best else json.loads(open(os.path.join(S, "fit2_cy.txt")).read().splitlines()[0])
    p.update(SANE_LO=12.0, SANE_HI=58.0)
    p.update(c["fix"])
    return p


_plays = {}


def plays(key):
    if key not in _plays:
        c = TEAMS[key]
        seqs = []
        srcs = ([(c["dir"], 1)] if c["dir"] else []) + [(OURS_DIR, 3)]
        for d, w in srcs:
            cur = None
            for kind, o, act, ex in tapes.team_decisions(d, c["name"], c["entry"]):
                k2 = (ex["fight"], ex["seat"])
                if k2 != cur:
                    cur = k2
                    seqs.append((w, []))
                seqs[-1][1].append((kind, o, act, ex))
        _plays[key] = seqs
    return _plays[key]


def tape_loss(key, params):
    qe = qn = rok = rn = mok = mn = 0.0
    for w, seq in plays(key):
        bot = cal_core.Core()
        bot.P = dict(cal_core.Core.P, **params)
        for kind, o, act, ex in seq:
            if kind == "move":
                mok += w * (bot.move(o) == act); mn += w
            elif kind == "quote":
                g = bot.quote(o)
                if act is not None:
                    qe += w * min(abs(g - act), 15.0); qn += w
            else:
                g = bot.respond(o, ex["price"])
                g = max(-10 - o.position, min(g, 10 - o.position))
                rok += w * (g == act); rn += w
    return qe / qn + 6 * (1 - rok / rn) + 4 * (1 - mok / mn)


def cal_loss(key, params, deals, tag):
    c = TEAMS[key]
    path = f"cand/{key}_{tag}.py"
    build.write(path, f"cand_{key}", params)
    t = cal.run([path], tuple(c["tgt"]), deals=deals, seeds=(1, 2))[os.path.abspath(path)]
    out = {o: t[o][0] for o in c["tgt"]}       # all from the side of OUR bot / the house bot
    return sum(WT[o] * abs(out[o] - c["tgt"][o]) for o in c["tgt"]), out


def main():
    key, iters = sys.argv[1], int(sys.argv[2])
    deals = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    rnd = random.Random(7)
    best = init_params(key)
    t0 = tape_loss(key, best)
    cl, out = cal_loss(key, best, deals, "work")
    bl = cl + 0.5 * t0
    print(f"start tape {t0:.3f} cal {cl:.3f}", {k: round(v, 2) for k, v in out.items()}, flush=True)
    space = {k: v for k, v in SPACE.items() if k not in TEAMS[key]["fix"]}
    if key == "qt":
        for k in ("W", "C_Q", "HIDE", "SKEW_Q"):
            space.pop(k, None)
        space.update(MIR_LO=(-20, 10), MIR_HI=(60, 100))
    for it in range(iters):
        c = dict(best)
        names = list(space) + list(CHOICE)
        for k in rnd.sample(names, rnd.choice((1, 1, 2, 3))):
            if k in CHOICE:
                c[k] = rnd.choice(CHOICE[k])
            else:
                lo, hi = space[k]
                c[k] = round(rnd.uniform(lo, hi), 3) if rnd.random() < 0.35 else \
                    round(min(hi, max(lo, best.get(k, (lo + hi) / 2) + rnd.gauss(0, (hi - lo) * 0.1))), 3)
        tl = tape_loss(key, c)
        if tl > t0 + 1.0 or 0.5 * tl > bl:
            continue
        cl, out = cal_loss(key, c, deals, "work")
        l = cl + 0.5 * tl
        if l < bl:
            best, bl = c, l
            print(f"{it} tape {tl:.3f} cal {cl:.3f}", {k: round(v, 2) for k, v in out.items()}, flush=True)
            json.dump(best, open(f"best_{key}.json", "w"))
    json.dump(best, open(f"best_{key}.json", "w"))
    print("BEST", json.dumps(best), flush=True)


if __name__ == "__main__":
    main()
