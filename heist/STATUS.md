# Heist status (the one file to look at)

Updated 18:00, Thu 8 Oct. The arena warned of calls over 50 ms: speed-hardened final = marseille. Since 15:40 the house bots no longer count and uploads are limited to one every 15 minutes.

| | File | Why |
|---|---|---|
| FINAL | heist/marseille.py = heist/professor.py (#636) | bogota's strategy, 30-40% faster; live +0.02 vs bogota; level with Imposters, ahead of PaperHands / MNC / Genz7 / TeenPatti on the same opponents |
| BEST LIVE | heist/bogota.py (= test_ee01_nudgeall.py, #611, up 16:45; = professor.py) | +0.06 +-0.08 vs palermo; >= palermo against every top team (Imposters #615 +1.98, MNC +2.95, Techy #606 +0.57) |
| ALSO PROVEN | heist/palermo.py (#591) | best live file: +0.43 +-0.38 vs the 30% nudge #588, +0.61 vs stockholm, +1.17 vs rio on real teams; wins back Imposters (+1.91), QuantXAlpha (+1.86), TeenPatti (+2.77), AJ (+0.74) |
| UPLOAD NOW | heist/bogota.py (re-upload after the z02 test), then heist/test_ll01_oppswap.py | bogota = the final; ll01 = half of palermo's undo (may win back Blind_Ambition / HAN SOLO) |
| FALLBACK (proven live) | heist/bogota.py or heist/palermo.py | re-upload if a test comes out worse |

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
| #611 | bogota (test_ee01_nudgeall) | +0.06 +-0.07 vs palermo (n=41); 49 of 52 won | +4.37 on real teams |
| #621 | test_z02_topbogota | -0.45 +-0.61 vs bogota; 41 of 42 won; top-10 teams equal | rejected for the final |

Still losing to: PaperHands -1.60, HAN SOLO -1.67, Genz7 -1.04 (palermo).

Plan: live tests every 15-20 minutes until about 20:00; from 21:00 only files with a live record; final = best live
record on real teams, copied to heist/professor.py, uploaded about 1-2 hours before close.
