# Farm line ledger

Goal: farm typical opponents (ai_typical, hider) as hard as the best bots without losing the
wins against the strong bots. Numbers: tools/eval.py --deals 300 --seeds 1 2 (default pool).
On the same setting the parent bridge_v01 scores Pool +9.63, Weighted +8.10,
vs r1 +2.73, vs r2 -2.41, vs r3 +3.13, vs ai_typical +8.12, vs hider +5.64.

| Version | Parent | Branch | Pool | Weighted | vs r1 | vs r2 | vs r3 | Idea |
|---|---|---|---|---|---|---|---|---|
| farm_v02 | bridge_v01 | farm | +10.16 | +8.87 | +2.72 | -2.39 | +3.16 | typical-AI profile in identifier + planner: ai_typical +8.12 -> +20.13 (W +0.78 +-0.04; seeds 5 6 +0.79) |
| farm_v03 | farm_v02 | farm | +10.25 | +8.93 | +2.72 | -2.41 | +3.16 | guard quote vs detected hider (exact public quote after round 1, nothing else): hider +5.64 -> +7.59 (W +0.055 +-0.019; seeds 5 6 +0.071) |
| farm_v04 | farm_v03 | farm | +10.30 | +8.97 | +2.72 | -2.39 | +3.16 | exact hider hand-sum set from its answers; planner steers/harvests it when <= 3 sums left: hider +7.59 -> +8.80 (W +0.047 +-0.017; seeds 5 6 +0.032) |

## Rejected ideas

| # | Parent | Idea | Result (seeds 1 2 unless noted) |
|---|---|---|---|
| R1 | farm_v02 | guard quoting (bridge_9 style) against EVERY unidentified opponent | W +0.39 +-0.24, hider +3.6, but rival_1 -1.54, rival_3 -1.73, mid_bayes -1.96: fails the rival rule |
| R2 | farm_v02 | guard vs hider counted from round 1 (any public quote, 0.02 or 0.0055 tolerance) | W +0.077, hider +3.1 but sharp-family -0.07..-0.09: an exactly average hand also opens at 105.0; kept the round-2 rule instead |
| R3 | farm_v03 | guard skew sweep vs hider: K 0 / 0.3 / 0.7 / 1.0, cap 1.5 / 6 | all within +-0.15 of K 0.5 cap 3 (noise): flat |
| R4 | farm_v03 | lot size in the Bayesian answer likelihood (1 lot = edge 2..3, weight 0.8) for every opponent | W +0.017 +-0.060, hider +0.11: noise |
| R5 | farm_v04 | hider planner threshold HSET_MAX 1 / 2 / 5 (vs hider only) | +8.59 / +8.64 / +8.87 vs +8.80 at 3: kept 3 |
