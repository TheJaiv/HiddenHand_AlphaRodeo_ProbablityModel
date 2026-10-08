# Heist status (the one file to look at)

Updated 16:40, Thu 8 Oct. Since 15:40 the house bots no longer count and uploads are limited to one every 15 minutes.

| | File | Why |
|---|---|---|
| BEST LIVE | heist/palermo.py (= test_y01_topfix.py, #591, up 15:55; = professor.py) | best live file: +0.43 +-0.38 vs the 30% nudge #588, +0.61 vs stockholm, +1.17 vs rio on real teams; wins back Imposters (+1.91), QuantXAlpha (+1.86), TeenPatti (+2.77), AJ (+0.74) |
| UPLOAD NOW | heist/test_ee01_nudgeall.py (from 16:45) | palermo + nudge also against readers; local gate passed on two seed pairs |
| FALLBACK (proven live) | heist/palermo.py (#591) | re-upload it if a test comes out worse |

Live results on real teams (paired: same opponent uploads, newest minus the previous):

| Entry | File | Paired result | Rank / score |
|---|---|---|---|
| #486 | tokyo | reference | |
| #495 | nairobi | +0.03 vs tokyo on real teams (its gain was the house bots) | |
| #505 | rio | +0.86 +-0.39 vs nairobi | |
| #513 / #561 / #565 / #573 | moscow / helsinki / lisbon / e01 | all within +-0.06 of each other | |
| #569 | test_j01_safeq (safe quoting) | -0.85 +-0.82 vs lisbon | |
| #586 | stockholm (15% nudge) | +0.46 +-0.23 vs lisbon | |
| #588 | test_u01_nudge30 (30% nudge) | +0.13 +-0.16 vs stockholm | #3 at +4.59 |
| #591 | palermo | +0.43 +-0.38 vs #588 | #4 at +4.29 after 47 fights (still filling) |
| #596 | test_aa01_naive06 (P_NAIVE 0.6) | -0.91 +-0.64 vs palermo | rejected |
| #601 | test_bb01_step2 | -0.07 +-0.10 vs palermo | #4 at +4.48 |
| next | test_ee01_nudgeall | pending | |

Still losing to: PaperHands -1.60, HAN SOLO -1.67, Genz7 -1.04 (palermo).

Plan: live tests every 15-20 minutes until about 20:00; from 21:00 only files with a live record; final = best live
record on real teams, copied to heist/professor.py, uploaded about 1-2 hours before close.
