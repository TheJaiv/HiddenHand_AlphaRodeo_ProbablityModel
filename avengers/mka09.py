"""avengers/mka09.py - build avengers/cand/a09_thresh.py: per-hypothesis answer thresholds.

Adds TH_PRIOR {(2, .7), (5, .2), (7, .1)} per hypothesis: the opponent takes when
|their fair - my price| > TH (the live field mostly takes at 5-7, our old model assumed 2).
Used in _see response likelihood, imm(), _roll(), and the post-imm position update.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "heist", "moscow.py")
OUT = os.path.join(HERE, "cand", "a09_thresh.py")

s = open(SRC).read()

REPS = [
    # hypothesis field index
    ("H_READS, H_RULE, H_LAM, H_TAU, H_KAP, H_MO, H_MT, H_P00, H_P01, H_P11, H_LW, H_SK = range(12)",
     "H_READS, H_RULE, H_LAM, H_TAU, H_KAP, H_MO, H_MT, H_P00, H_P01, H_P11, H_LW, H_SK, H_TH = range(13)"),
    # prior constant
    ("LAM_PRIOR = ((1.0, 0.45), (0.7, 0.12), (0.4, 0.08), (0.0, 0.35))",
     "LAM_PRIOR = ((1.0, 0.45), (0.7, 0.12), (0.4, 0.08), (0.0, 0.35))\n"
     "TH_PRIOR = ((2.0, 0.7), (5.0, 0.2), (7.0, 0.1))   # their take threshold: |fair - my price|"),
    # _init non-blend
    ("                    for kap, pk in KAP_PRIOR:\n"
     "                        lw = math.log((1 - P_BLEND) * pr * pl * pt * pk)\n"
     "                        H.append([reads, rule, lam, tau, kap, mu, T_MEAN if reads else 0.0,\n"
     "                                  var, 0.0, T_SD * T_SD if reads else 1e-6, lw, 0.0])",
     "                    for kap, pk in KAP_PRIOR:\n"
     "                        for th, pth in TH_PRIOR:\n"
     "                            lw = math.log((1 - P_BLEND) * pr * pl * pt * pk * pth)\n"
     "                            H.append([reads, rule, lam, tau, kap, mu, T_MEAN if reads else 0.0,\n"
     "                                      var, 0.0, T_SD * T_SD if reads else 1e-6, lw, 0.0, th])"),
    # _init blend
    ("                    for sk, ps in BLEND_SK:\n"
     "                        lw = math.log(P_BLEND * pl * pt * pk * ps)\n"
     "                        H.append([False, BLD, lam, tau, kap, mu, W_MEAN,\n"
     "                                  var, 0.0, W_SD * W_SD, lw, sk])",
     "                    for sk, ps in BLEND_SK:\n"
     "                        for th, pth in TH_PRIOR:\n"
     "                            lw = math.log(P_BLEND * pl * pt * pk * ps * pth)\n"
     "                            H.append([False, BLD, lam, tau, kap, mu, W_MEAN,\n"
     "                                      var, 0.0, W_SD * W_SD, lw, sk, th])"),
    # _see response band: move lo/hi into the h loop
    ("        if not is_quote:\n"
     "            can_buy = pos > -10\n"
     "            can_sell = pos < 10\n"
     "            if qty > 0:\n"
     "                lo, hi = price + 2, INF\n"
     "            elif qty < 0:\n"
     "                lo, hi = -INF, price - 2\n"
     "            else:\n"
     "                lo = price - 2 if can_sell else -INF\n"
     "                hi = price + 2 if can_buy else INF\n"
     "                if lo == -INF and hi == INF:\n"
     "                    return\n",
     "        if not is_quote:\n"
     "            can_buy = pos > -10\n"
     "            can_sell = pos < 10\n"
     "            if qty > 0:\n"
     "                kind = 1\n"
     "            elif qty < 0:\n"
     "                kind = -1\n"
     "            else:\n"
     "                kind = 0\n"
     "                if not can_buy and not can_sell:\n"
     "                    return\n"),
    ("            else:\n"
     "                my = A0 + A1 * mt + (B0 + B1 * mt) * mo + extra",
     "            else:\n"
     "                th = h[H_TH]\n"
     "                if kind > 0:\n"
     "                    lo, hi = price + th, INF\n"
     "                elif kind < 0:\n"
     "                    lo, hi = -INF, price - th\n"
     "                else:\n"
     "                    lo = price - th if can_sell else -INF\n"
     "                    hi = price + th if can_buy else INF\n"
     "                my = A0 + A1 * mt + (B0 + B1 * mt) * mo + extra"),
    # imm
    ("        def imm(h, V, p):\n"
     "            f, sf, c = resp_dist(h, p)\n"
     "            zb = (f - p - 2) / sf\n"
     "            zs = (p - 2 - f) / sf\n"
     "            return (nb * ((p + 2 - V) * Phi(zb) - beta * c * pdf(zb))\n"
     "                    + ns * ((V - p + 2) * Phi(zs) - beta * c * pdf(zs))), f",
     "        def imm(h, V, p):\n"
     "            f, sf, c = resp_dist(h, p)\n"
     "            th = h[H_TH]\n"
     "            zb = (f - p - th) / sf\n"
     "            zs = (p - th - f) / sf\n"
     "            return (nb * ((p + th - V) * Phi(zb) - beta * c * pdf(zb))\n"
     "                    + ns * ((V - p + th) * Phi(zs) - beta * c * pdf(zs))), f"),
    # extra candidates around the 2nd hypothesis' fair (wide-threshold take boundary)
    ("        cands = [bp, f0[0], f0[0] + 3.05, f0[0] - 3.05]",
     "        cands = [bp, f0[0], f0[0] + 3.05, f0[0] - 3.05]\n"
     "        if len(f0) > 1:\n"
     "            cands += [f0[1] + 6.05, f0[1] - 6.05]"),
    # quote() post-imm position update
    ("                x, f = imm(h, V, p)\n"
     "                e = f - p\n"
     "                ps = pos\n"
     "                if e > 2:\n"
     "                    ps -= nb\n"
     "                elif e < -2:\n"
     "                    ps += ns",
     "                x, f = imm(h, V, p)\n"
     "                e = f - p\n"
     "                ps = pos\n"
     "                if e > h[H_TH]:\n"
     "                    ps -= nb\n"
     "                elif e < -h[H_TH]:\n"
     "                    ps += ns"),
    # _roll take conditions
    ("                e = f - p\n"
     "                if e > 2:\n"
     "                    n = min(2, 10 + pos)\n"
     "                    pos -= n\n"
     "                    pnl += n * (p + 2 - V)\n"
     "                elif e < -2:\n"
     "                    n = min(2, 10 - pos)\n"
     "                    pos += n\n"
     "                    pnl += n * (V - p + 2)",
     "                e = f - p\n"
     "                th = h[H_TH]\n"
     "                if e > th:\n"
     "                    n = min(2, 10 + pos)\n"
     "                    pos -= n\n"
     "                    pnl += n * (p + 2 - V)\n"
     "                elif e < -th:\n"
     "                    n = min(2, 10 - pos)\n"
     "                    pos += n\n"
     "                    pnl += n * (V - p + 2)"),
]

miss = 0
for old, new in REPS:
    if old not in s:
        print("MISSING:", old[:80].replace("\n", "\\n"))
        miss += 1
    else:
        s = s.replace(old, new, 1)
if miss:
    sys.exit(f"{miss} patches missing")
s = s.replace("# Version: moscow (v05), parent denver, idea:",
              "# Version: cand a09_thresh, parent moscow, idea:", 1)
open(OUT, "w").write(s)
print("wrote", OUT)
