# Heist ledger (branch `heist`)

Judge: the live field. Local tests only against calibrated imitations of live teams (heist/opp_*.py).

Naming: each accepted bot takes the next name in this order, never reused:
tokyo (v00, reference), berlin (v01), nairobi (v02), rio (v03), denver (v04), moscow (v05), helsinki (v06),
oslo (v07), lisbon (v08), stockholm (v09), palermo (v10), bogota (v11), marseille (v12), manila (v13);
the list ended there, so the next city code names from the show follow: pamplona (v14), then matias (v15).
professor.py = a copy of whichever bot is chosen as the FINAL upload (its 4th line names the original).

| Version | Name | Parent | Field model gain (seeds) | Live paired vs previous upload | Idea |
|---|---|---|---|---|---|
| v00 | tokyo | versions/hunt_v10.py | - | best paired live record so far (entry #452) | reference |
| v01 | berlin | tokyo | house bots (exact, seeds 1-3 x 400): reader +3.0, sharp +0.9, naive 0.0 | #459 / #466 (same code) vs #452: +0.07 +-0.20 (n=51), +0.11 +-0.21 (n=49) | = versions/hunt_v14.py: blend quoters with lam 0.2, blend-only trade-learning prior, crush of exact house readers |
| v02 | nairobi | berlin | house bots (exact, seeds 1-3 x 400): reader +7.5 (31.0 vs 23.6), sharp +9.7 (29.6 vs 20.0), naive 0.0; field weight 2/57 -> about +0.30. Decisions identical to berlin in all 418 cached live fights except vs house reader / sharp | #495 (10:21): vs #466 berlin +0.39 (n=45): differs ONLY vs reader +7.4, sharp +10.0 (no false trigger on 400 deals x 45 teams); vs #486 tokyo +0.41 +-0.54 (n=57) | exact house-reader attack (merge line's planner), only after two quotes fit the reader formula to 0.005; off at the first unexpected answer. Slowest quote 3.7 ms |
| v03 | rio | nairobi | calibrated imitations (opp_happy_happy_463, opp_paperhands, opp_teenpatti: live within 1.5), seeds 1-3 and 4-7: Happy +2.5 / +3.4, PaperHands +2.3 / +3.0, TeenPatti +2.1 / +2.4; house bots +0.05..+0.5; other new imitations +1.7..+2.9 | #505 (10:41) vs #495 nairobi: +0.93 +-0.39 (n=50; Balls +4.5, IITBHU +4.5, Trade Transmitters +3.1; alpha -2.4, Quantumlesssss -1.7) | swap only in round 5. Field model (22 calibrated imitations + house, seeds 4 5): rio +5.68, nairobi +3.76, tokyo +3.30; rio - nairobi +1.92 +-0.15 |
| v04 | denver | rio | field model vs rio: seeds 4 5 +0.114 +-0.049, seeds 6 7 +0.115 +-0.051 (all opponents within -0.3..+0.5) | not uploaded alone (bundled into moscow) | first quote of the deal = public estimate |
| v05 | moscow | denver | field model vs denver (c14_oppswap06): seeds 4 5 +0.105 +-0.062, 6 7 +0.129 +-0.059, 8 9 +0.109 +-0.063, 10 11 (800 deals) +0.077 +-0.044 -> above 2 se on 6 7 and 10 11; gains vs followers (Genz7, Pokemons, QuantXAlpha, QUANTUMLYSTUPID +0.5..+0.6), costs vs non-swappers (naive -0.7) | #513 (11:02) vs #505 rio: +0.04 +-0.19 (n=52): neutral live (expected +0.2) | price in the opponent's coming swap (K 0.6) |
| v06 | helsinki | moscow | field model vs moscow, 800 deals: seeds 10 11 +0.855 +-0.069, seeds 12 13 +0.865 +-0.071 (avengers captain_america, same idea with the fill-price bug: +0.706 +-0.070); biggest gains Pokemons +2.7, Happy463 +2.8, ThunderX +2.2, Phantom +2.0, QUANTUMLYSTUPID +2.0, Godtier +1.7; costs HAN SOLO -0.8, Double Dividend -0.8, Quant Qods -0.3 | #561 (13:28) vs #513 moscow: -0.03 +-0.34 (n=49): neutral. Gains Dark Pool +2.7, Godtier +2.6, OptiMystics +2.3, Cyberpsycho +2.2, QUANTUMLYSTUPID +1.9; costs Techy -1.9, HAN SOLO -1.9, ThunderX -1.8, Imposters -1.6, Double Dividend -1.3 | per-hypothesis opponent take threshold 2 / 7 + P_NAIVE 0.45 |

| v07 | oslo | helsinki | field model vs helsinki (800 deals): seeds 10 11 +0.116 +-0.049, seeds 12 13 +0.200 +-0.049 | not uploaded alone (in lisbon) | P_NAIVE 0.45 -> 0.3 |
| v08 | lisbon | oslo | field model: no-op (no double peekers in it); decisions = oslo except vs teams that peek twice in a deal | #565 (13:48) vs #561 helsinki: -0.02 +-0.26 (n=57): neutral; peeker defence HURT: Quants Treasure #514 -0.65 (helsinki +0.01), Team How #549 -1.41 -> defence dropped | peeker defence: after 2 opponent peeks, quote 1.3 from its last quote, take only with 3 more points of edge (QT: top teams +8 more than us) |

| v09 | stockholm | oslo | field model vs helsinki (800 deals): old field seeds 12 13 +0.304 +-0.050, 14 15 +0.311 +-0.049; refreshed field2 seeds 12 13 +0.183 +-0.064, 14 15 +0.169 +-0.065 | #586 (15:19): vs #565 lisbon +0.43 +-0.22 (n=48), vs #561 helsinki +0.44 +-0.29, vs #573 e01 +0.53 +-0.35; #2 at +5.45 (53/59 wins). Gains alpha +2.5, Blind +2.2, OptiMystics +2.8, Code Riders +2.6; costs PaperHands -1.3, Quant Qods -1.3, Sattebaaz -1.2 | quote moved 15% towards the safe quote unless reader / limit + no paid probes / model crush (house attack kept) |

| v10 | palermo | stockholm | (y01) field2 +0.016 vs the 30% nudge (no calibrated top team locally) | #591 (15:55): vs #588 +0.43 +-0.38 (n=46), vs stockholm +0.61 +-0.37, vs rio +1.17 +-0.82; top teams: Imposters +1.91 (was -0.48), QuantXAlpha +1.86, TeenPatti +2.77, AJ +0.74; still PaperHands -1.60, Genz7 -1.04, HAN SOLO -1.67 | 30% quote nudge + undo moscow's public first quote and opponent-swap pricing |

| v11 | bogota | palermo | (ee01) field2 +0.099 +-0.014 (12 13), +0.074 +-0.013 (14 15); old field +0.051 +-0.010 | #611 (16:45): +0.06 +-0.08 vs palermo (n=30), +0.17 +-0.15 vs bb01; vs newest top teams: Imposters #615 +1.98, MNC #594 +2.95, Techy #606 +0.57, QuantXAlpha +2.35, TeenPatti +2.79; still PaperHands -1.46, HAN SOLO -1.63, Genz7 -0.84 | the 30% quote nudge also against confident readers |

| v12 | marseille | bogota | field2 vs bogota +0.014 +-0.009 (fast02 exact: -0.001, fast03 prune 8: +0.002); same-play check: 32 of 720 plays differ; speed: median 0.20 vs 0.29 ms, p99 0.99 vs 1.18 ms, total -32%; vs naive p99 0.59 vs 0.84 ms | #636 (17:50): +0.02 +-0.07 vs bogota (n=44), 47 of 50 won; vs leaders (same opponents): Imposters +0.01, PaperHands #638 +0.35, MNC +0.86, Genz7 +1.09, TeenPatti +0.95 | speed only (arena warned of calls over 50 ms): answer model cached per quote, fused Kalman step, heapq top-N, PRUNE 12 -> 6 |

| v13 | manila | marseille | (nn05) field2 vs marseille +0.087 +-0.028 (seeds 12 13), +0.078 +-0.026 (14 15); swap-bar trend: 6 -0.060, 4 0, 2.5 +0.026, 1 +0.054, 0 +0.083 | #665 (18:48): +0.101 +-0.047 vs marseille (n=37; better on 27, worse on 9), +0.13 vs bogota; vs leaders on the same opponents +0.09..+0.12 each (Imposters +0.04, PaperHands #667 +0.35, MNC +1.02, Genz7 +1.24, TeenPatti +0.96); head to head Imposters +2.33 (marseille +1.84), Genz7 -0.90 (-1.06), still LOSES to PaperHands (#658 -1.24, #667 -1.32; marseille -1.48 / -1.32) and HAN SOLO (-1.57) | swap in round 5 whenever the expected gain is positive (SWAP_TH round 5: 4 -> 0) |

| v14 | pamplona | manila | (qq02) field2 vs manila +0.115 +-0.016 (12 13), +0.129 +-0.018 (14 15); weight 0.3 on the expected position +0.014 more, 0.7 worse | #689 (19:10): +0.401 +-0.134 vs manila (n=24 at 19:25; better on 23, worst Code Riders -0.02); PaperHands #667 +0.84, Imposters #688 +1.24, TeenPatti +1.19, Techy +0.71, MNC +0.45, Genz7 +0.34, HAN SOLO +0.30 | round-5 swap decided by the average of the current and the expected final position |

## Candidates and rejected ideas

| Candidate | Change | Local | Live | Verdict |
|---|---|---|---|---|
| c01_swap4 | tokyo, never swap before round 4 (top teams swap in r4/r5) | house bots: naive +0.1, reader +0.3, sharp +0.4 | never uploaded | superseded by c04 on nairobi |
| c04_swap3 / swap4 / swap5 / swap5lo / noswap | nairobi, first swap round 3 / 4 / 5 / 5 with a lower bar / never | seeds 4-7 vs Happy463, PaperHands, TeenPatti: +1.4/+1.4/+0.7, +2.4/+2.3/+1.7, +3.4/+3.0/+2.4, = swap5, +0.2/+0.7/+0.4 (naive -3.3) | - | swap5 -> rio |
| c02_safeq | tokyo, quote their last quote +-1.3 towards my value unless a confident reader / at the limit | house bots: naive -3.0, reader -3.2, sharp -2.0 | not uploaded | rejected: gives up the maker edge against honest quoters and readers |
| c03 (depth 4) | = nairobi with depth 4 in round 2 | reader +31.6, sharp +28.9 | - | slowest quote 9.4-10.2 ms under load; depth 3 in round 2 (nairobi) is as good and under 4 ms |

Tools (heist/): census.py (standings + fight list -> data/matrix.json), replays.py (fight pages -> data/fights/),
match_replay.py (does a file make a team's live decisions?), samedec.py (do two files decide alike on live replays?),
feval.py (cached local score matrix), teamprof.py / follow.py / follow2.py / profile1.py / pnlsplit.py (replay profiles).
Our live entries identified from replays: #452 = #486 = tokyo; #459, #466 = hunt_v13/v14 family (berlin); #473, #481 match no saved file.
| c05_pubfirst | rio, first quote of the deal = the public estimate | field model seeds 4 5: +0.114 +-0.049, seeds 6 7: +0.115 +-0.051 vs rio | - | passes -> denver |
| c06_hide30 | rio, every planner quote moved 30% of (my hand - average) towards an average hand | field model: -0.896 +-0.163 (naive -4.8, QUANTSTATIC -2.2, Quant Qods -2.1) | - | rejected |
| c09_pblend25 | rio, P_BLEND 0.12 -> 0.25 | field model: +0.053 +-0.050 / +0.064 +-0.052 | - | not significant on either seed pair |
| c10_risk30 / c10_risk120 | rio, RISK 60 -> 30 / 120 | field model: +0.046 +-0.028 and +0.057 +-0.027 / -0.077 +-0.037 | - | fails one seed pair / rejected |
| c11_pen1 | rio, 1 point extra edge per lot when answering | field model: +0.035 +-0.075 | - | not significant |
| c12_boffset | denver, blend quoters with a constant step (0 / +1.3 / -1.3) | field model: -0.008 +-0.030 | - | rejected |
| c13_r1lot | denver, answer at most 1 lot in round 1 | field model: -0.060 +-0.047 | - | rejected |
| c14_oppswap06 / 10 | denver, price in the opponent's coming swap, K 0.6 / 1.0 | K 0.6: see moscow; K 1.0: -0.001 +-0.073 | - | K 0.6 -> moscow |
| c15_pen23a/b/c | denver, extra taker edge in rounds 2-3 (we lose as taker there against every fitted team) | +0.001 / +0.036 / +0.089 (+-0.06) | - | not significant |
| c16_sigq10 / 15 | denver, SIG_Q 0.5 -> 1.0 / 1.5 | 1.0: seeds 4 5 +0.102 +-0.058, 6 7 +0.136 +-0.062, 8 9 +0.079 +-0.061, 10 11 (800) +0.048 +-0.043; 1.5: +0.069 +-0.067 | - | to be re-tested on moscow |
| c17_safeq | denver, safe quote (their last quote +-1.3) unless reader / at the limit | field model: -1.149 +-0.121 | - | rejected again (on the calibrated field) |
| c18_late | denver, take more readily in rounds 4-5 (-0.5 per lot) | -0.035 +-0.015 | - | rejected |
| c19_sigq10 | moscow, SIG_Q 1.0 | seeds 10 11 (800): +0.048 +-0.043 | - | marginal; superseded |
| c20_wmean07 / c21_pb25w07 | moscow, W_MEAN 0.7 / + P_BLEND 0.25 | not finished (machine overloaded) | - | open |
| c22_peekdef | moscow, after 2 opponent peeks: safe quote + 3 points taker margin | field model: +0.001 (no 2-peekers in it); QT imitation (not calibrated): -2.2 | - | open: only a live test can tell (QT: top teams +8 more than us) |
| c23_thfix | = avengers/captain_america with the fill price fixed | +0.855 +-0.069 / +0.865 +-0.071 vs moscow | - | -> helsinki |

## Avengers line (other session, stopped)

avengers/captain_america.py = moscow + take-threshold hypotheses (2 / 7) + P_NAIVE 0.45. Checked here (heist field model,
seeds 10 11, 800 deals): +0.706 +-0.070 vs moscow. Its immediate-profit formula books a taker's fill at price + threshold
instead of price + 2; heist's helsinki is the same idea with that fixed (+0.15 better). Its follow-up candidates b01-b11 were
all flat or negative; its imitations of Cyberpsycho / Imposters / QT / Godtier / Trade Transmitters are not calibrated.
| d01_th6040 / d02_th257 / d04_sigq10 | helsinki, threshold prior 2/7 at 0.6/0.4 / thresholds 2/5/7 / SIG_Q 1.0 | +0.004 / -0.006 / -0.035 (+-0.04) | - | rejected |
| d03_naive03 | helsinki, P_NAIVE 0.3 | +0.116 / +0.200 (+-0.049) | - | -> oslo |
| c24_honestswap / c24h | moscow / helsinki, early swap only vs 'honest' quoters (rio's late swap cost -1..-2.4 vs alpha, DD, Bayes, Quantumlesssss) | -0.347 +-0.037 / -0.133 +-0.027 | - | rejected: the honesty test also fires on PaperHands / Techy |

Lesson (13:45): the field model over-predicts live gains (rio +1.9 local / +0.85 live; moscow +0.2 / 0.0; helsinki +0.86 / 0.0).
Structural changes found from live data (house attack, swap timing) are what moved the live score.
| f01_picky | helsinki, 1.5 more edge to take in rounds 1-3 | -0.071 +-0.053 | - | rejected |
| g01_th027 | helsinki, take thresholds 0 / 2 / 7 | -0.024 +-0.030 | - | rejected |
| h01_noprobe | helsinki, no paid probes / model crush (house attack kept) | +0.000 +-0.008 (probes almost never fire) | - | rejected: no effect |
| i01_lam0 / i02_liar | helsinki, more 'quotes say nothing' / add 'quotes against their hand' (lam -0.5) | -0.086 +-0.038 / -0.143 +-0.039 | - | rejected |
| j01_safeq | helsinki, safe quote (top teams' style) unless confident reader / limit / house attack | house bots: naive -1.1, reader -0.2, sharp -2.2; earlier on moscow (c17) -1.15 on the field model | #569 (14:09): -0.85 +-0.82 vs lisbon (n=58) | rejected: safe quoting gives away the maker edge (local said -1.3) |

Finding (14:00, live fight pages): against the mid-field the top teams make far more PnL per deal than we do
(ThunderX: PaperHands +23.4, Imposters +17.9, us +1.3; Pokemons: +26.0 / +11.1 / +3.3; MNC: +23.2 / +12.8 / +6.6;
Blind_Ambition: +29.7 / +19.1 / +7.5; Double Dividend: +24.6 / +13.2 / +4.2). It is extraction, not consistency.
| e01_thonly (test_e01_thonly.py) | moscow + take thresholds, no P_NAIVE change | field model +0.558 vs moscow | #573 (14:29): -0.06 +-0.19 vs helsinki (n=53), +0.03 +-0.20 vs moscow | equal: five planner versions (rio, moscow, helsinki, lisbon, e01) all about +5.3 live |
| p01_follow / p02_follow2 | helsinki, P_BLEND 0.3 + W_MEAN 0.7 / P_BLEND 0.3 | refreshed field (field2): -0.082 +-0.060 / -0.144 +-0.055 | - | rejected |
| m01_swap4 / m02_swap4big | helsinki, swap from round 4 / round 4 only if gain > 10 | field2: -0.348 +-0.048 / -0.296 +-0.042 | - | rejected (round 5 stays) |
| k01_earlycap / k02_widetaker | helsinki, |pos| <= 4 before round 4 / 3 more taker edge every round | +0.019 +-0.018 / -0.284 +-0.081 | - | rejected |

14:45 field refresh: 24 teams had uploaded newer entries since 10:30; all refetched (12 fights each) and refitted; calibration
against 9 of our live files: 16 imitations within mean 1.5 of every planner-family file (data/field2.json).
Oracle check (35 opponents all five planner versions fought): best single version +6.57, best version per opponent +7.32
(part of that is selection noise); a per-opponent switch needs an in-deal detector, and the 'honest' detector misfired (c24).
| q01_blend30 / q02_blend15 | helsinki, quote moved 30% / 15% towards the safe quote | old field -0.068 / +0.008; field2 +0.091 / +0.097 | - | q02 -> stockholm bundle |
| r01_onelot | helsinki, 1-lot answers allowed | -0.033 / -0.031 | - | rejected |
| h01_noprobe (field2) | helsinki, no probes | field2 +0.016 +-0.011 (ThunderX imitation: one probe quote 146.18 cost -100 in a deal) | - | -> stockholm bundle |

## 15:40 rule change: house bots out of the arena score

The arena rules now say the house bots play no part in the score (only a 5-deal naive load check), and uploads are limited
to one every 15 minutes. All fights were re-run without them. Live paired results recomputed without house fights:
nairobi - tokyo +0.03 (the house attack no longer counts), rio - nairobi +0.86 +-0.39, moscow / helsinki / lisbon / e01 all
within +-0.06 of each other, stockholm - lisbon +0.46 +-0.23, - helsinki +0.47 +-0.31, - e01 +0.56 +-0.37, - rio +0.63 +-0.67.
Real-team means (old fights): Imposters +5.31, TeenPatti +4.94, Genz7 +4.71, PaperHands +4.67, stockholm +4.44.
heist/field.py now leaves the house bots out (HOUSE=1 to add them).
| u01_nudge30 (test_u01_nudge30.py) | stockholm, nudge 30% | field2 (no house) +0.098 +-0.047 | #588 (15:43): real teams +4.59 (#3), vs #586 stockholm +0.13 +-0.16 (n=55), vs lisbon +0.63 +-0.32, vs e01 +0.66 +-0.34 | best live so far, not significant vs stockholm |
| w01_step2 / w02_early / w03_nudge45 | 30% nudge with step 2.0 / only rounds 2-3 / 45% | field2 vs stockholm +0.136 / +0.083 / +0.059 (+-0.05) | - | w01 queued |
| y01_topfix (test_y01_topfix.py) | 30% nudge minus moscow's public first quote and opponent-swap pricing | field2 +0.016 +-0.079 (field2 has no calibrated top team) | sent 15:55 | live test: those two changes cost 0.5-0.9 vs PaperHands, Genz7, Imposters |

Top-team trade-off (live, real teams): rio beat PaperHands +0.40, Genz7 +0.55, Imposters +0.82; every later version lost to
them (stockholm: PaperHands -1.57, Genz7 -1.11, Imposters #574 -0.77; 30% nudge: -1.73 / -0.54 / -0.48) while gaining more on
the mid-field. With top teams likely to upload their best at the end, the final must not give these matchups away.
| x01 / x02 | 30% nudge scaled by (1 - P(reader)) | field2 -0.018 / -0.036 vs stockholm | - | rejected |
| z01_rionudge30 | rio + 30% nudge + no probes | field2 -0.854 +-0.112 vs the 30% nudge | - | parked (risky) |
| aa01_naive06 (test_aa01_naive06.py) | palermo with P_NAIVE 0.6 | field2 -0.551 +-0.090 vs palermo | #596 (16:12): -0.91 +-0.64 vs palermo (n=26): HAN SOLO +3.0, AJ +1.4 but QuantXAlpha -2.8, Pokemons -4.1, Imposters -1.0 | rejected |
| bb01_step2 (test_bb01_step2.py) | palermo, safe-quote step 1.3 -> 2.0 | field2 +0.037 +-0.035; bb02 (22% nudge) -0.026 | #601 (16:30): -0.07 +-0.10 vs palermo (n=45) | tie |

## Endgame (drafted 16:30)

- Final = the file with the best paired live record on real teams (house bots no longer count), checked against the current
  newest entry of every team, especially the top ten (they are likely to upload their best at the end).
- It is copied to heist/professor.py (4th line names the original) and committed; validate + speed checked again.
- Optional decoy: an older file (e.g. heist/tokyo.py) in the early evening so other teams do not tune against our final,
  then the final uploaded 1-2 hours before close (never in the last minutes). Needs the exact deadline from the organisers.
- Current best live: manila (#665, v13) +0.10 +-0.05 over marseille (#636); professor.py = manila since 19:00.
| cc01_nudge40 | palermo, nudge 40% | field2 +0.021 +-0.040 | - | flat: 30% stays |
| dd01_clip5 / dd02_clip8 | palermo, clip my quote to +-5 / +-8 of the safe quote | field2 -0.162 / -0.107 | - | rejected: shrinking beats clipping |
| ee01_nudgeall (test_ee01_nudgeall.py) | palermo, nudge also against confident readers | field2 seeds 12 13 +0.099 +-0.014, 14 15 +0.074 +-0.013; old field +0.051 +-0.010 | #611: +0.06 +-0.08 vs palermo | -> bogota |
| gg01 / gg02 | ee01 with soft compression of large deviations (k 20 / 10) | field2 -0.085 / -0.193 vs ee01 | - | rejected: large planner deviations carry value |
| hh01 / hh02 | ee01 + 1 / 2 more points of taker edge | field2 -0.098 / -0.382 vs ee01 | - | rejected |
| ii01_nor5 / ii02_step07 | bogota, no nudge in round 5 / step 0.7 | field2 -0.022 / -0.028 | - | rejected |
| z02_topbogota (test_z02_topbogota.py) | bogota minus take thresholds / P_NAIVE (= rio + 30% nudge for everyone + no probes) | field2 -0.948 +-0.104 vs bogota | #621 (17:09): 41 wins of 42, only loss Cyberpsycho -0.87; but -0.45 +-0.61 vs bogota (n=38); top-10 teams shared: +1.18 vs bogota +1.16 (Genz7 +0.8 / HAN SOLO +1.6 / AJ +2.7 better, TeenPatti / QuantXAlpha worse) | rejected for the final: lower average; bogota stays |

### 17:40 equal-footing check (top team score minus bogota #611's, same opponent uploads, real teams)
Imposters #615 -0.05 (n=53), PaperHands #624 -0.90 (n=35), MNC #594 -1.10 (n=51), Genz7 #262 -1.15 (n=52),
TeenPatti #330 -0.99 (n=53). On equal footing bogota is level with Imposters and ahead of every other top team; the
standings' raw means differ because entries played different opponent sets. Remaining gaps: Blind_Ambition (top
teams +3.7..+6.6 more) and HAN SOLO (+3.1..+4.9); both swing +-3 between our versions.
| ll01_oppswap (test_ll01_oppswap.py) | bogota + opponent-swap pricing back (half of palermo's undo) | field2 -0.056 +-0.050 | #629 (17:26): -0.02 +-0.20 vs bogota (n=39); vs leaders weaker (Imposters -0.17 vs +0.05, TeenPatti +0.66 vs +0.99) | rejected: tie, bogota stays |
| ll02_pubfirst (test_ll02_pubfirst.py) | bogota + public-estimate first quote back (the other half) | field2 -0.035 +-0.067 | not uploaded | dropped for the speed fix |

### 17:30 our versions vs the leaders (ours minus theirs on shared opponent uploads, real teams)
| Ours minus | rio | stockholm | 30% nudge | palermo | bogota | z02 |
|---|---|---|---|---|---|---|
| Imposters #615 | -1.00 | -0.60 | -0.46 | +0.02 | +0.05 | -0.65 |
| PaperHands #624 | -0.29 | +0.47 | +0.65 | +1.08 | +1.22 | +0.37 |
| MNC #594 | -0.75 | +0.08 | +0.15 | +0.80 | +1.10 | +0.37 |
| Genz7 #262 | -0.22 | +0.28 | +0.31 | +0.95 | +1.15 | +0.43 |
| TeenPatti #330 | -0.08 | +0.34 | +0.40 | +0.90 | +0.99 | +0.27 |
bogota is the best of our versions against every leader.
| fast01 / fast02 (speed, exact) | bogota with the answer model cached per quote + heapq / + fused Kalman step | identical play on 600 plays; -13% total time | - | folded into marseille |
| fast03_prune8 / fast04_prune6 | fast02 with PRUNE 8 / 6 | field2 +0.002 / +0.014; 3 / 28 of 600 plays differ; -25% / -40% total time | - | fast04 -> marseille |

17:50 arena team page ("Problems in your fights", only our team sees it) for ll01 #629: "Time limit exceeded: a call took over
50 ms ... x2" - 2 calls in about 1.4 million (58 fights x 400 deals x 2 seats x ~30 calls): negligible, consistent with rare
machine pauses (locally even 0.03 ms move() calls occasionally spike to 9 ms). marseille cuts the work per call by 30-40%.
| mm01_naive015 / mm02_risk30 | marseille, P_NAIVE 0.15 / RISK 30 | field2 -0.107 +-0.059 / +0.001 +-0.023 | - | rejected locally |
| mm03_th6040 (test_mm03_th6040.py) | marseille, take-threshold prior 2 / 7 at 0.6 / 0.4 | field2 +0.022 +-0.070 | #647 (18:10): -0.53 +-0.32 vs marseille (n=41), -0.43 vs bogota, -0.39 vs ll01; 41 of 45 won; worst Pokemons #641 -4.4, Sattebaaz -2.1, MNC -1.7; vs leaders worse (Imposters -0.76 vs +0.01) | rejected: more weight on the 7-point threshold hurts live |
| mm04_nudge40 (test_mm04_nudge40.py) | marseille, nudge 40% | (cc01 on palermo: field2 +0.021) | #656 (18:30): -0.00 +-0.12 vs marseille (n=44), 46 of 50 won, board #2 at +4.35; on the same 43 opponents equal to marseille against every leader (Imposters +0.11 vs +0.10, PaperHands +0.33 vs +0.32, MNC +1.07 vs +1.06, Genz7 +1.22 both, TeenPatti +1.15 vs +1.16) | tie: 30% stays |

18:40 equal footing (marseille #636 minus each leader's newest, same 43 opponent uploads): Imposters +0.10, PaperHands #643 +0.32, MNC +1.06, Genz7 +1.22, TeenPatti +1.16, HAN SOLO +1.99, Techy #642 +0.50, QuantXAlpha +1.24, AJ +1.84. Head to head marseille still loses to PaperHands (-1.3..-1.5), HAN SOLO (-1.6), Genz7 (-1.1).
| nn01_swap25 (test_nn01_swap25.py) | marseille, round-5 swap bar 4 -> 2.5 | field2 seeds 12 13: +0.029 +-0.016; seeds 14 15: +0.023 +-0.016 | - | passes (2 seed pairs) |
| nn02_swap6 | marseille, round-5 swap bar 4 -> 6 | field2 seeds 12 13: -0.060 +-0.023 | - | rejected (lower bar is the right direction) |
| nn03_nplan8 (test_nn03_nplan8.py) | marseille, plan with the 8 likeliest hypotheses (NPLAN 6 -> 8) | field2 seeds 12 13: +0.083 +-0.060; seeds 14 15: +0.056 +-0.063; speed under load: quote median 0.64 vs 0.50 ms | held (not uploaded) | fails the second seed pair |
| nn04_swap1 (test_nn04_swap1.py) | marseille, round-5 swap bar 4 -> 1 | field2 seeds 12 13: +0.049 +-0.023; seeds 14 15: +0.059 +-0.023 (bar 6 -0.060, 4 0, 2.5 +0.023..+0.029) | not uploaded (nn05 went up instead) | superseded by nn05 |
| nn05_swap0 (test_nn05_swap0.py) | marseille, round-5 swap bar 4 -> 0 (swap whenever the expected gain is positive) | field2 seeds 12 13: +0.087 +-0.028; seeds 14 15: +0.078 +-0.026 | #665 (18:48): +0.101 +-0.047 vs marseille (n=37) | -> manila (v13) = professor.py |
| pp01_nplan8 (test_pp01_nplan8.py) | manila, NPLAN 6 -> 8 | field2 vs manila +0.079 +-0.058 (12 13), +0.056 +-0.062 (14 15); on marseille +0.083 / +0.056 | queued behind qq02 | fails the 2nd seed pair narrowly; positive in all 4 runs |
| pp02_deltas | manila, 10 stage-1 price offsets instead of 6 | +0.012 +-0.024 / +0.020 +-0.025 | - | rejected (flat) |
| qq01_swappos | manila, round-5 swap decided by the current position instead of the expected final position | field2 vs manila +0.059 +-0.023 (12 13), +0.053 +-0.024 (14 15) | - | passes; superseded by qq02 |
| qq02_swapmix (test_qq02_swapmix.py) | manila, round-5 swap decided by the average of the current and the expected final position | field2 vs manila +0.115 +-0.016 (12 13), +0.129 +-0.018 (14 15) | #689: +0.40 +-0.13 vs manila (n=24) | -> pamplona (v14) = professor.py |
| qq03_swap37 / qq04_swap73 | qq02 with weights 0.3 / 0.7 on the expected final position (0.7 / 0.3 on the current one) | vs qq02: +0.014 +-0.006 / +0.014 +-0.008; -0.059 +-0.011 / -0.066 +-0.013 | - | weight 0.3 slightly better than 0.5 (too small to see live); qq02 stays the probe |
| rr01_roll05 | qq02, play-out of the rest of the deal weighted 0.5 in quote / respond | vs qq02 +0.089 +-0.125 (12 13), +0.122 +-0.124 (14 15) | - | not significant (noisy) |
| rr02_roll075 (test_rr02_roll075.py) | qq02, play-out of the rest of the deal weighted 0.75 in quote / respond | vs qq02 +0.297 +-0.075 (12 13), +0.263 +-0.078 (14 15) | #701 (19:27): vs pamplona -0.356 +-0.333 at n=14 (worse on 10), -0.112 +-0.274 at n=26; vs manila +0.31, vs marseille +0.43 (its swap part) | rejected: the play-out weight does not hold up live; final = pamplona |

19:36 FINAL: heist/professor.py = pamplona (v14), live #689 +0.40 +-0.13 vs manila. Last test rr02 (#701) rejected.
19:45 FINAL UPLOADED: heist/professor.py as committed here = pamplona's code byte for byte, with the version line and the description docstring removed by the user before upload (1,076 lines; code lines are 36 lower than in pamplona.py).
20:08 final #713 (professor.py as uploaded): 41 fights, 38 won, mean +3.37; = pamplona +0.002 +-0.010 (n=24); vs manila +0.33 +-0.13, vs marseille +0.37 +-0.13. Equal footing (ours minus theirs, same opponents): Imposters #722 +0.16, PaperHands #712 +0.42, MNC +1.68, Genz7 +1.98, TeenPatti +1.22, HAN SOLO +2.19, QuantXAlpha +1.88. Head to head vs PaperHands #712 -0.56. Board #4 at 3.48 (37 fights) behind MNC 3.78 / Genz7 3.71 / TeenPatti 3.57, ahead of PaperHands 3.36 and Imposters 3.02.
