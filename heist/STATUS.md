# Heist status (the one file to look at)

Updated 15:58, Thu 8 Oct. House bots no longer count; upload limit now 15 minutes.

| | File | Why |
|---|---|---|
| LIVE NOW | heist/test_y01_topfix.py (sent 15:55) | 30% nudge minus moscow's two changes that cost vs top teams. Check vs #588 at about 16:20 |
| FALLBACK (proven live) | heist/test_u01_nudge30.py (#588) | real teams +4.59 (#3); +0.13 vs stockholm #586 (+0.46 vs lisbon); house bots no longer count since 15:40 |
| NEXT IN QUEUE | heist/cand/e01_thonly.py (moscow + take thresholds, no P_NAIVE change) | only if lisbon loses more to Imposters / Genz7 than helsinki did: separates helsinki's two changes live |

Live results so far (paired: same opponent uploads, our newest minus the previous):

| Entry | File | Paired result | Rank / score |
|---|---|---|---|
| #486 | tokyo | reference | |
| #495 | nairobi | +0.41 vs tokyo (house reader +7.4, sharp +10.0, nothing else changed) | |
| #505 | rio | +0.85 +-0.37 vs nairobi | #2 at +5.43 (11:00) |
| #513 | moscow | +0.04 +-0.19 vs rio | #4 at +5.35 |
| #561 | helsinki | -0.03 +-0.34 vs moscow | #4 at +5.38 |
| #565 | lisbon | -0.02 +-0.26 vs helsinki; peeker defence hurt (QT -0.65, Team How -1.4) | #4 |
| #569 | test_j01_safeq (safe quoting) | -0.85 +-0.82 vs lisbon | #6 while live |
| #573 | test_e01_thonly | -0.06 +-0.19 vs helsinki; +0.03 vs moscow | #3 at +5.29 |
| #586 | stockholm | +0.46 +-0.23 vs lisbon (real teams) | #2 (with house) |
| #588 | test_u01_nudge30 | +0.13 +-0.16 vs stockholm | #3 at +4.59 (real teams) |
| next | test_y01_topfix | pending | |

Plan to the deadline: keep testing structural ideas live until about 20:00; from 21:00 only files that already have a live record;
upload the chosen final (copied to heist/professor.py) about 1-2 hours before close.
