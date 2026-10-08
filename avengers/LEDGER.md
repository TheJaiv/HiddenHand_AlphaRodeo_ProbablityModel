# Avengers ledger (folder `avengers/`)

Judge: the live field. Local tests only against calibrated imitations of live teams
(heist/opp/*.py + new ones in avengers/opp/). Same game, same rules as heist/.

Naming: each accepted bot takes the next name in this order, never reused:
ironman (v00), captain_america (v01), thor (v02), hulk (v03), black_widow (v04),
hawkeye (v05), vision (v06), scarlet_witch (v07), black_panther (v08), spider_man (v09),
doctor_strange (v10), captain_marvel (v11), ant_man (v12).
assemble.py = a copy of whichever avenger is chosen as the FINAL upload (its 4th line names the original).

| Version | Name | Parent | Field model gain (seeds) | Live paired vs previous upload | Idea |
|---|---|---|---|---|---|
| v00 | ironman | heist/denver | - | - | avengers baseline = heist denver (deal's first quote = public estimate) |
| v01 | captain_america | heist/moscow | vs moscow: seeds 4 5 +0.665 +-0.097, seeds 6 7 +0.750 +-0.099 (both >6 SE); every opponent at or above tokyo | pending | per-hypothesis opponent take thresholds TH in {2,7} (field's best take at 5-7 edge, we assumed 2) + P_NAIVE 0.6->0.45. Slowest call 2.0 ms |

## Candidates and rejected ideas

| Candidate | Change | Local | Live | Verdict |
|---|---|---|---|---|
| a01_j1public | moscow, both seats' first quote = public estimate | seeds 4 5: -0.217 +-0.065 | - | rejected (hiding hand info from followers in r1 hurts: their carried quote misprices for us) |
| a02_delta812 | moscow, DELTAS += 8, 12 | -0.006 +-0.011 | - | rejected (no effect) |
| a03_carry065 / a03_carry10 | moscow, CARRY 0.65 / 1.0 | -0.042 / +0.020 | - | rejected (n.s.) |
| a04_naive045 | moscow, P_NAIVE 0.6 -> 0.45 | seeds 4 5 +0.135 +-0.066, seeds 6 7 +0.220 +-0.066 | - | accepted -> folded into captain_america |
| a05_blend018 | moscow, P_BLEND 0.18 | -0.006 +-0.031 | - | rejected |
| a07_swpth3 | moscow, SWAP_TH r5 4 -> 3 | +0.022 +-0.009 / +0.018 +-0.009 | - | not >2 SE of anything meaningful (effect too small) |
| a08_probe075 | moscow, P_PROBE 0.75 | -0.015 +-0.010 | - | rejected |
| a09_thresh | moscow, TH_PRIOR {2,5,7} per hypothesis | seeds 4 5 +0.268 +-0.089, seeds 6 7 +0.404 +-0.085 | - | accepted mechanism; 5.7-9 ms under load -> replaced by 2-value a09b |
| a09b_th27 | moscow, TH_PRIOR {2,7} | seeds 4 5 +0.308 +-0.088, seeds 6 7 +0.453 +-0.085 | - | accepted -> folded into captain_america |

## Field model extensions (avengers/opp/)

New imitations built here (heist left these uncalibrated), each checked against live scores
of our own files like heist/calib.py does.

| Imitation | Entry | Live vs local (our files) | Verdict |
|---|---|---|---|
