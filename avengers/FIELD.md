# The live field — avengers view (avengers/FIELD.md)

Forked from heist/FIELD.md (census 10:39) and refreshed 11:02. Live arena data only; every live fight
uses one hidden 400-deal set per opponent pair, so paired comparisons of our uploads have no deal noise.

Our entries: #505 = rio (heist v03) is our current newest live upload. Moscow (v05) is the heist line's
next accepted file (not yet live at 11:02).

## Standings (census 11:02)

| # | Team | Score | Won | Newest | us (#505) vs it |
|---|---|---|---|---|---|
| 1 | PaperHands | +5.92 | 53/57 | v11 | +1.50 |
| 2 | Techy Traders | +5.74 | 51/57 | v16 (#502) | +0.23 |
| 3 | Imposters | +5.72 | 56/57 | #457 | +0.82 |
| 4 | **Alpha Rodeo** | **+5.43** | 54/57 | #505 | - |
| 5 | Genz7 | +4.86 | 49/57 | #262 | +0.55 |
| 6 | TeenPatti | +4.79 | 51/57 | #330 | +0.86 |
| 7 | MNC Traders | +4.36 | 43/57 | #346 | +2.30 |
| 8 | AJ_The_Trader | +3.98 | 45/57 | #344 | +2.50 |
| 9 | Pokemons | +3.93 | 48/57 | #214 | +1.35 |
| 10 | HAN SOLO | +3.92 | 49/57 | #375 | +1.46 |

Gap to #1: ~0.49. Teams keep uploading; the final field is their newest at close.

## Who beats us, whom we beat (rio #505, 11:02 matrix)

Only Cyberpsycho #316 (-0.96) beats us. Godtier -0.08 and Quants Treasure -0.01 are coin flips.
Everything else is a win, biggest: House reader +31.6, OptiMystics +11.8, Dalal Street +11.2,
Apex +9.0, Outliers +8.8, Bulls +8.3.

## Styles (replay profiling, avengers/prof/)

- **Threshold followers** (quote ≈ opponent's last quote + own hand barely shows; take only at 5-7
  points of edge; never in round 1 for the best of them): Cyberpsycho, Imposters, Godtier,
  Quants Treasure, Trade Transmitters, TeenPatti, Happy Happy, Techy. This is the dominant field style.
  - Cyberpsycho #316 (fit, seed 2): quote = blend(own last quote 0.48, own fair 0.52) − 3.5-ish step,
    reads our quotes T≈0.83 (SANE 60), TH≈7, never takes in round 1 (R1L 0), swaps from round 5.
  - Quants Treasure #480: quote ≈ our quote + small stuff (W 1.0, C −2.5, T 0.53, TH 6.3, ASYM −3.2
    sells more readily than it buys, R1L 1).
  - Imposters #457: W 0.42, C −0.86, T 0.09, TH 7.0 / TH2 7.7, ASYM +4.3 (buys far more readily),
    R1L 1, swap r4, SKEW +1.2 per lot of their position.
  - Godtier #465: honest-ish (W 0.17, T 0.14), TH 7, R1L 0, swap r5.
- **Readers** (quote = house-formula with trust ~0.8-1): house reader/sharp, Apex, Bulls, Money Heist,
  Hidden Alpha. We harvest +8..+31 from these with the exact-reader attack and the general planner.
- **Honest quoters**: Pravichayah, Quant Qods, Chanakya, QUANTSTATIC (+5..+7 for us).
- **House bots** are part of the real field (3 of ~57 teams).

Key consequence: our planner long assumed opponents take at |edge| > 2. The field's best teams take at
5-7. The avengers line adds per-hypothesis take thresholds (a09/a09b, TH ∈ {2, 7}), the largest single
local gain yet: +0.27 (seeds 4,5) / +0.45 (seeds 6,7) on the calibrated field model over moscow.

## Field model (used for local acceptance)

heist/opp/ calibrated list (25 entries incl. house bots, weights per heist/data/field.json) plus
avengers/opp/ imitations for the teams that beat us, once calibrated (calib5):

| Imitation | Entry | Live vs local (our files) | Verdict |
|---|---|---|---|
| opp_cyberpsycho | 316 | (see avengers/data/calib5.txt) | |
| opp_quants_treasure | 480 | | |
| opp_godtier | 465 | | |
| opp_trade_transmitters | 371 | | |
| opp_imposters | 457 | | |

Teams with no cached replays yet (newest uploads too fresh): Happy Happy #496, Techy #502, Chill Chips #493,
KRYPTEX #503, Team How #500 — imitations pending replay data.
