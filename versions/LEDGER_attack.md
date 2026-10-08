# Attack line ledger

Branch of the bridge line that squeezes more out of the parts that already work (look-ahead vs
identified readers, moves, first quote, respond margins, constants). Numbers are tools/eval.py
--deals 300 on seeds 1 2 (diff vs parent in brackets, +-2se); "conf 5 6" is the same diff on seeds 5 6.

| Version | Parent | Branch | Pool | Weighted | vs r1 | vs r2 | vs r3 | Idea |
|---|---|---|---|---|---|---|---|---|
| bridge_v01 | - | lab | +9.62 | +8.09 | +2.73 | -2.41 | +3.13 | starting point (re-measured on this machine, 300 deals) |
| attack_v02 | bridge_v01 | attack | +10.57 | +8.80 | +2.73 | -2.41 | +3.09 | planner may try the 195 / 0 extreme quote at any position, not only at +-10 lots (W +0.71+-0.15; conf 5 6 +0.88+-0.15; slowest 4.2 ms) |
| attack_v03 | attack_v02 | attack | +11.33 | +9.61 | +4.05 | -1.69 | +3.60 | swap bar falls by round: 30 / 20 / 10 in rounds 3 / 4 / 5 (W +0.82+-0.09; conf 5 6 +0.77+-0.10; slowest 6.4 ms) |
| attack_v04 | attack_v03 | attack | +11.97 | +10.15 | +4.05 | -1.70 | +3.60 | a PAID extreme quote (195 / 0 short of the limit) only after 2+ consistent reader quotes (W +0.54+-0.08; conf 5 6 +0.40+-0.08; slowest 1.1 ms) |
| attack_v05 | attack_v04 | attack | +12.35 | +10.58 | +3.57 | +0.44 | +4.00 | the deal's very first quote (nothing known yet) is the public estimate, hiding my hand (W +0.44+-0.12; conf 5 6 +0.40+-0.12; vs r1 -0.48 on 1 2 and -0.56 on 5 6 (borderline), vs r2 +2.1 / +2.5; slowest 1.0 ms) |
| attack_v06 | attack_v05 | attack | +12.53 | +10.80 | +3.99 | +0.93 | +4.08 | stronger inventory skew: at 6+ lots quote 0.8 per lot against my position (was 0.2) (W +0.23+-0.04; conf 5 6 +0.18+-0.04; slowest 7.8 ms under load) |

## Rejected ideas

(diff in WEIGHTED vs the parent named, seeds 1 2)
- HARVEST_OUT 3.02 -> 2.02 (harvest just outside a reader's band): -0.82 vs bridge_v01 (the planner models sharp sizing, 1 lot at edge < 3; big losses vs sharp / mid_exact / swapper).
- EXT_FROM 8 (paid extreme quote only from 8 lots): +0.17 vs bridge_v01, superseded by EXT_FROM 0 (attack_v02).
- BIG_STEPS (6, 15): paid steers of 6 / 15 points as the first quote of a plan: +0.03+-0.02 vs attack_v02 (too small to keep).
- PEEK at round 2 when belief sd > 6 (unidentified opponent): +0.00+-0.03 vs attack_v02 (peek never pays its 3 here).
- RESP_MARGIN 0.2 -> 0.0: +0.07+-0.03 vs bridge_v01, but -0.02+-0.02 on top of attack_v02.
- SWAP_TH (999, 45, 30, 30, 30) (allow a round-2 swap at a high bar): -0.03+-0.07 vs attack_v02.
- SWAP_TH (999, 999, 30, 25, 20): +0.47+-0.07 vs attack_v02, beaten by 30 / 20 / 10 (attack_v03).
- SWAP_TH (999, 999, 25, 15, 5): -0.04+-0.06 vs attack_v03.
- SWAP_TH (999, 999, 20, 10, 0): -0.40+-0.09 vs attack_v03 (swapping on any positive gain is too loose).
- EXT_NQ 3 (paid extremes after 3+ reader quotes): -0.02+-0.12 vs attack_v03 (too late: reader -4.4); EXT_NQ 2 kept (attack_v04).
- FIRST_ALPHA 0.2 (first quote mostly hidden): +0.32+-0.10 vs attack_v04, r1 -0.62: worse than fully hidden (attack_v05).
- STEER_IN 1.98 -> 1.5: -0.01+-0.02 vs attack_v04.
- HARVEST_OUT 3.02 -> 3.5: -0.07+-0.03 vs attack_v04.
- DEPTH 4 -> 5: -0.00+-0.02 vs attack_v04 (slower, no gain).
- RESP_MARGIN 0.2 -> 0.5: -0.02+-0.03 vs attack_v04.
- WIDE 0.15 -> 0.10 / 0.20: -0.01+-0.03 / -0.01+-0.03 vs attack_v05.
- NOISE 0.5 -> 0.0: -0.16+-0.08 vs attack_v05 (r1 -2.0: an exactly honest quote is read by rival_1); NOISE 1.0: -0.00+-0.08.
- SKEW sweep vs attack_v05: 0.0 -0.18, 0.3 +0.05, 0.4 +0.11, 0.6 +0.18, 0.8 +0.23 (kept, attack_v06), 1.2 +0.03 (mid_bayes -0.76).
