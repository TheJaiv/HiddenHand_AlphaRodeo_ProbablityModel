"""Joint calibration: tape loss + LAM * (2*|r1 - arena| + mean |house - arena|)."""
import json, random, sys
from multiprocessing import Pool
import agg, fitcore as F
SPACE = dict(T=(0,2,"f"), W=(0,1,"f"), SKEW_Q=(-4,4,"f"), C_Q=(-3,3,"f"), SKEW_R=(-1,4,"f"), TH1=(0.5,7,"f"), TH2=(0.5,8,"f"),
             HIDE=(-1,1,"f"), TRADE_EV=(-1,4,"f"), T_PRICE=(0,0,[True,False]), AVG_Q=(0,0,[1,2,3]),
             TB=(0,0,[0,1]), TB_G=(-1,2,"f"), TB_F=(0,1,"f"))
def aerr(pool, key, p):
    t = agg.TARGET[key]
    jobs = [("core", p, o, 300, s) for o in ("r1", "r2") if o in t for s in (71, 72)] + [("core", p, o, 300, 71) for o in t if o not in ("r1", "r2")]
    res = pool.map(agg._job, jobs)
    out = {o: sum(x[2] for x in res if x[0] == o) / sum(1 for x in res if x[0] == o) for o in t}
    house = [abs(out[o] - t[o]) for o in t if o not in ("r1", "r2")]
    main = sum(2 * abs(out[o] - t[o]) for o in ("r1", "r2") if o in t)
    return main + (sum(house) / len(house) if house else 0), out
if __name__ == "__main__":
    key, iters, lam = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
    import os
    src = f"final2_{key}.json" if os.path.exists(f"final2_{key}.json") else None
    best = dict(F.core.Core.P, **(json.load(open(src)) if src else json.loads(open(f"fit2_{key}.txt").read().splitlines()[0])))
    space = {k: v for k, v in SPACE.items() if not (key == "qt" and k in ("W", "C_Q", "HIDE", "SKEW_Q"))}
    rnd = random.Random(11)
    with Pool(2) as pool:
        tl = F.loss(F.evaluate(key, best)); ae, out = aerr(pool, key, best); bl = tl + lam * ae
        print("start", round(tl, 3), round(ae, 3), {k: round(v, 2) for k, v in out.items()}, flush=True)
        for it in range(iters):
            c = dict(best)
            for k in rnd.sample(list(space), rnd.choice((1, 1, 2, 3))):
                lo, hi, kind = space[k]
                c[k] = (round(rnd.uniform(lo, hi), 3) if rnd.random() < 0.35 else round(min(hi, max(lo, best[k] + rnd.gauss(0, (hi - lo) * 0.07))), 3)) if kind == "f" else rnd.choice(kind)
            tl = F.loss(F.evaluate(key, c))
            if tl > bl: continue
            ae, out = aerr(pool, key, c); l = tl + lam * ae
            if l < bl:
                best, bl = c, l
                print(it, round(tl, 3), round(ae, 3), {k: round(v, 2) for k, v in out.items()}, flush=True)
        json.dump(best, open(f"final3_{key}.json", "w")); print("BEST", json.dumps(best), flush=True)
