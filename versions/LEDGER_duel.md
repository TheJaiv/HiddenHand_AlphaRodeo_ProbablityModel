# Duel line ledger

Goal: win the head-to-heads against the strongest bots (rival_2 first). Numbers are eval.py scores,
seeds 1 2, 300 deals (score scale), unless stated. Acceptance: see versions/LEDGER.md plus the
duel rule (vs rival_2 rises by more than its error bar, confirmed on seeds 5 6, r1/r3 not down > 0.5).

| Version | Parent | Branch | Pool | Weighted | vs r1 | vs r2 | vs r3 | Idea |
|---|---|---|---|---|---|---|---|---|
| bridge_v01 | - | lab | +9.63 | +8.10 | +2.73 | -2.41 | +3.13 | starting point (same seeds 1 2 x 300 basis) |
| duel_v02 | bridge_v01 | duel | +9.79 | +8.31 | +3.02 | -0.71 | +3.33 | opponent swap: kept 4 cards are all >= / <= the discard (mixture prior); r2 +1.70 +-0.46 (s56 +2.15 +-0.47), weighted +0.21 +-0.04 |
| duel_v03 | duel_v02 | duel | +10.48 | +9.03 | +4.03 | -0.09 | +3.75 | from round 2 shade quote 40% toward the average hand (hide my hand); vs v02: r2 +0.62 +-0.43 (s56 +0.75 +-0.46), weighted +0.74 +-0.10 (s56 +0.71) |
| duel_v04 | duel_v03 | duel | +10.55 | +9.11 | +4.14 | +0.26 | +3.95 | SKEW 0.4, +0.6 taker margin rounds 4-5 (unidentified opp), probe quotes >22 from public ignored by belief; vs v03 weighted +0.073 +-0.035 (s56 +0.042 +-0.034), r2 +0.35 +-0.16 (s56 +0.16 +-0.17, not confirmed alone: accepted on the weighted clause) |

## Rejected ideas

- c1 (on bridge_v01): 4th 'flat' belief component (opponent quotes carry no information): belief error vs rival_2 unchanged (rmse 8.7-11.9), not pursued.
- c4a / c4b (on v02): wider quote sigmas (4/10) or more weight on the hiding component: belief error vs rival_2 unchanged, not pursued.
- c5 (on v02): hide 30% / 60% of my hand in every round: r2 +1.13 / +2.06 but r3 -0.48 / -1.44 (rival_3 exploits a quote that is shaded from round 1).
- c6 (on v02): hide coefficient random per deal U(0.1, 0.5) every round: r2 +1.04, r3 -0.60.
- c7 (on v02): hide 45% in rounds 1-3 only, honest after: r2 +1.08, r3 -1.76, weighted +0.02.
- c8b (on v02): hide 40% from round 3 only: r2 +0.14 +-0.31 (not significant), weighted +0.47.
- c9a (on v03): hide 60% instead of 40%: r3 -0.62, weighted -0.05.
- c9b (on v03): WIDE 0.30 (taker margin per sd): r2 -0.30, r3 -0.46.
- c10a / c10b / c10c (on v03): response FLOOR 0.05 / TRUST 0.5 / SIG_A 1.5: all worse (weighted -0.29 / -0.64 / -0.12).
- c11a / c11b (on v03): response FLOOR 0.003 / SIG_A 0.5: flat (weighted -0.08 / -0.03).
- c12 alone (on v03): ignore probe quotes: r2 +0.08 +-0.11, weighted +0.05 +-0.05 (kept only inside v04).
- c13a / c13b alone (on v03): late margin +0.6 (r2 +0.11 +-0.09) / SKEW 0.4 (r2 +0.23 +-0.09): combined into v04.
- c14s6 (on v03): v04 with SKEW 0.6: r2 +0.45 but r1 -0.21, weighted +0.13 (below v04's +0.16 on the subset).
- c15 (on v04): also hide 15% in round 1: r1 -0.38, r2 -0.01, weighted -0.11.
