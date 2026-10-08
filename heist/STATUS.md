# Heist status (the one file to look at)

Updated 19:27, Thu 8 Oct. The arena warned of calls over 50 ms: speed-hardened final = marseille. Since 15:40 the house bots no longer count and uploads are limited to one every 15 minutes.

| | File | Why |
|---|---|---|
| FINAL | heist/pamplona.py = heist/professor.py (#689) | manila + round-5 swap decided by the average of current and expected final position; live +0.40 +-0.13 vs manila (better on 23 of 24) |
| PREVIOUS FINAL | heist/manila.py (#665) | marseille + swap in round 5 whenever the expected gain is positive; live +0.10 +-0.05 vs marseille (better on 27 of 37 opponents), +0.1 vs every leader on the same opponents |
| PREVIOUS FINAL | heist/marseille.py (#636) | bogota's strategy, 30-40% faster; level with Imposters, ahead of PaperHands / MNC / Genz7 / TeenPatti |
| BEST LIVE | heist/bogota.py (= test_ee01_nudgeall.py, #611, up 16:45; = professor.py) | +0.06 +-0.08 vs palermo; >= palermo against every top team (Imposters #615 +1.98, MNC +2.95, Techy #606 +0.57) |
| ALSO PROVEN | heist/palermo.py (#591) | best live file: +0.43 +-0.38 vs the 30% nudge #588, +0.61 vs stockholm, +1.17 vs rio on real teams; wins back Imposters (+1.91), QuantXAlpha (+1.86), TeenPatti (+2.77), AJ (+0.74) |
| UPLOAD NOW | heist/test_rr02_roll075.py (pamplona + play-out weight 0.75; local +0.28 vs qq02) | last test before the final upload; final = rr02 only if it beats pamplona live, else professor.py (pamplona) |
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
| #629 | test_ll01_oppswap | -0.02 +-0.20 vs bogota | tie, rejected |
| #636 | marseille (final) | +0.02 +-0.07 vs bogota; 47 of 50 won | +4.41 on real teams |
| #647 | test_mm03_th6040 | -0.53 +-0.32 vs marseille (n=41) | rejected (rank 9 at +3.13 while newest) |
| #656 | test_mm04_nudge40 | -0.00 +-0.12 vs marseille (n=44); equal vs every leader on the same opponents | tie (board #2 at +4.35) |
| #665 | test_nn05_swap0 = manila (v13) | +0.101 +-0.047 vs marseille (n=37); 45 of 49 won | final until 19:25 |
| #689 | test_qq02_swapmix = pamplona (v14) | +0.401 +-0.134 vs manila (n=24, better on 23) | NEW FINAL |

Still losing to: PaperHands -1.60, HAN SOLO -1.67, Genz7 -1.04 (palermo).

Plan: live tests every 15-20 minutes until about 20:00; from 21:00 only files with a live record; final = best live
record on real teams, copied to heist/professor.py, uploaded about 1-2 hours before close.
