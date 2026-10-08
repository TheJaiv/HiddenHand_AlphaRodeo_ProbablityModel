# Heist ledger (branch `heist`)

Judge: the live field. Local tests only against calibrated imitations of live teams (heist/opp_*.py).

Naming: each accepted bot takes the next name in this order, never reused:
tokyo (v00, reference), berlin (v01), nairobi (v02), rio (v03), denver (v04), moscow (v05), helsinki (v06),
oslo (v07), lisbon (v08), stockholm (v09), palermo (v10), bogota (v11), marseille (v12), manila (v13).
professor.py = a copy of whichever bot is chosen as the FINAL upload (its 4th line names the original).

| Version | Name | Parent | Field model gain (seeds) | Live paired vs previous upload | Idea |
|---|---|---|---|---|---|
| v00 | tokyo | versions/hunt_v10.py | - | best paired live record so far (entry #452) | reference |
| v01 | berlin | tokyo | house bots (exact, seeds 1-3 x 400): reader +3.0, sharp +0.9, naive 0.0 | #459 / #466 (same code) vs #452: +0.07 +-0.20 (n=51), +0.11 +-0.21 (n=49) | = versions/hunt_v14.py: blend quoters with lam 0.2, blend-only trade-learning prior, crush of exact house readers |
| v02 | nairobi | berlin | house bots (exact, seeds 1-3 x 400): reader +7.5 (31.0 vs 23.6), sharp +9.7 (29.6 vs 20.0), naive 0.0; field weight 2/57 -> about +0.30. Decisions identical to berlin in all 418 cached live fights except vs house reader / sharp | #495 (10:21): vs #466 berlin +0.39 (n=45): differs ONLY vs reader +7.4, sharp +10.0 (no false trigger on 400 deals x 45 teams); vs #486 tokyo +0.41 +-0.54 (n=57) | exact house-reader attack (merge line's planner), only after two quotes fit the reader formula to 0.005; off at the first unexpected answer. Slowest quote 3.7 ms |
| v03 | rio | nairobi | calibrated imitations (opp_happy_happy_463, opp_paperhands, opp_teenpatti: live within 1.5), seeds 1-3 and 4-7: Happy +2.5 / +3.4, PaperHands +2.3 / +3.0, TeenPatti +2.1 / +2.4; house bots +0.05..+0.5; other new imitations +1.7..+2.9 | #505 (10:41) vs #495 nairobi: +0.93 +-0.39 (n=50; Balls +4.5, IITBHU +4.5, Trade Transmitters +3.1; alpha -2.4, Quantumlesssss -1.7) | swap only in round 5. Field model (22 calibrated imitations + house, seeds 4 5): rio +5.68, nairobi +3.76, tokyo +3.30; rio - nairobi +1.92 +-0.15 |
| v04 | denver | rio | field model vs rio: seeds 4 5 +0.114 +-0.049, seeds 6 7 +0.115 +-0.051 (all opponents within -0.3..+0.5) | not uploaded alone (bundled into moscow) | first quote of the deal = public estimate |
| v05 | moscow | denver | field model vs denver (c14_oppswap06): seeds 4 5 +0.105 +-0.062, 6 7 +0.129 +-0.059, 8 9 +0.109 +-0.063, 10 11 (800 deals) +0.077 +-0.044 -> above 2 se on 6 7 and 10 11; gains vs followers (Genz7, Pokemons, QuantXAlpha, QUANTUMLYSTUPID +0.5..+0.6), costs vs non-swappers (naive -0.7) | #513 (11:02) vs #505 rio: +0.04 +-0.19 (n=52): neutral live (expected +0.2) | price in the opponent's coming swap (K 0.6) |
| v06 | helsinki | moscow | field model vs moscow, 800 deals: seeds 10 11 +0.855 +-0.069, seeds 12 13 +0.865 +-0.071 (avengers captain_america, same idea with the fill-price bug: +0.706 +-0.070); biggest gains Pokemons +2.7, Happy463 +2.8, ThunderX +2.2, Phantom +2.0, QUANTUMLYSTUPID +2.0, Godtier +1.7; costs HAN SOLO -0.8, Double Dividend -0.8, Quant Qods -0.3 | pending (sent 13:30) | per-hypothesis opponent take threshold 2 / 7 + P_NAIVE 0.45 |

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
