"""Fit Core params to a team's tapes by teacher forcing.

score = quote MAE + RESP_W * respond mismatch rate (+ move mismatches)
"""
import random
import sys

import core
import tapes

TEAMS = {"q": ("quantumlesssss", "Quantumlesssss", 29), "ph": ("paperhands", "PaperHands", 26),
         "k": ("kryptex", "KRYPTEX", 45), "o": ("outliers", "Outliers", 34),
         "th": ("team_how", "Team How", 59), "tp": ("teenpatti", "TeenPatti", 8)}

import json as _json
for _k, _v in _json.load(open("teams2.json")).items():
    TEAMS[_k] = (_v["dir"], _v["name"], _v["entry"])

_cache = {}


def plays(key):
    if key not in _cache:
        d, t, e = TEAMS[key]
        out = []
        cur, seq = None, None
        for kind, o, act, ex in tapes.team_decisions(d, t, e):
            if "Void" in ex["opp"]:
                continue
            k2 = (ex["fight"], ex["seat"])
            if k2 != cur:
                cur = k2
                seq = []
                out.append(seq)
            seq.append((kind, o, act, ex))
        _cache[key] = out
    return _cache[key]


def evaluate(key, params, cls=core.Core, detail=False, rounds=None):
    qerr, rok, rn, mok, mn = [], 0, 0, 0, 0
    rows = []
    for seq in plays(key):
        bot = cls()
        bot.P = dict(cls.P, **params)
        for kind, o, act, ex in seq:
            if kind == "move":
                g = bot.move(o)
                mok += (g == act)
                mn += 1
            elif kind == "quote":
                g = round(bot.quote(o), 2)
                if act is not None and (rounds is None or ex["round"] in rounds):
                    qerr.append(abs(g - act))
                    rows.append((ex, act, g))
            else:
                g = bot.respond(o, ex["price"])
                g = max(-10 - o.position, min(g, 10 - o.position))
                if rounds is None or ex["round"] in rounds:
                    rok += (g == act)
                    rn += 1
    mae = sum(qerr) / len(qerr)
    within = sum(e < 0.5 for e in qerr) / len(qerr)
    res = dict(mae=mae, within=within, resp=rok / max(rn, 1), move=mok / max(mn, 1))
    if detail:
        return res, rows
    return res


def loss(res, resp_w=6.0):
    return res["mae"] + resp_w * (1 - res["resp"]) + 4 * (1 - res["move"])


def search(key, base, space, iters=300, seed=0, resp_w=6.0, cls=core.Core):
    rnd = random.Random(seed)
    best = dict(cls.P, **base)
    bres = evaluate(key, best, cls)
    bl = loss(bres, resp_w)
    for it in range(iters):
        cand = dict(best)
        for name in rnd.sample(list(space), k=min(len(space), rnd.choice((1, 1, 2, 3)))):
            lo, hi, kind = space[name]
            if kind == "f":
                if rnd.random() < 0.5:
                    cand[name] = round(rnd.uniform(lo, hi), 3)
                else:
                    cand[name] = round(min(hi, max(lo, best[name] + rnd.gauss(0, (hi - lo) * 0.08))), 3)
            else:
                cand[name] = rnd.choice(kind)
        res = evaluate(key, cand, cls)
        l_ = loss(res, resp_w)
        if l_ < bl:
            best, bres, bl = cand, res, l_
    return best, bres


if __name__ == "__main__":
    key = sys.argv[1]
    print(evaluate(key, {}))
