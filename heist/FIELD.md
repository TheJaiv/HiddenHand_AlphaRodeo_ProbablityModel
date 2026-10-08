# The live field (heist/FIELD.md)

Census 2026-10-08 10:39 from the public standings and fight list (heist/census.py; data in heist/data/). Every live fight uses the same hidden 400-deal set, so a deterministic bot scores exactly the same against an unchanged opponent upload: our paired live comparisons have no deal noise per opponent.

Our entries: #486 = tokyo, #495 = nairobi (berlin + exact house-reader attack).

## Top 15

| # | Team | Score | Won | Newest | nairobi #495 vs it | tokyo #486 vs it | Style (fit) |
|---|---|---|---|---|---|---|---|
| 1 | Imposters | +5.81 | 52/52 | #457 | -1.14 | -2.13 | blend |
| 2 | Genz7 | +4.89 | 47/53 | #262 | +0.59 | -0.29 | follower |
| 3 | TeenPatti | +4.79 | 48/53 | #330 | +0.21 | -1.06 | blend |
| 4 | Alpha Rodeo | +4.72 | 47/55 | #495 | - | - | - |
| 5 | MNC Traders | +4.39 | 41/54 | #346 | +1.26 | +0.12 | follower |
| 6 | PaperHands | +4.35 | 49/55 | #485 | +0.58 | +0.56 | follower |
| 7 | AJ_The_Trader | +4.10 | 45/55 | #344 | +3.21 | +2.53 | blend |
| 8 | HAN SOLO | +3.99 | 48/56 | #375 | +1.96 | +2.00 | honest |
| 9 | Pokemons | +3.90 | 48/56 | #214 | +1.18 | +0.81 | follower |
| 10 | QuantXAlpha | +3.85 | 43/56 | #458 | +0.24 | -0.23 | follower |
| 11 | The Risk Violators | +3.78 | 46/56 | #391 | +2.30 | +2.13 | blend |
| 12 | Chill Chips | +3.47 | 52/56 | #493 | -0.86 | -1.01 | - |
| 13 | Techy Traders | +3.36 | 36/47 | #502 | +5.44 | - | follower |
| 14 | Double Dividend | +3.30 | 40/56 | #453 | +2.41 | +2.51 | follower |
| 15 | Sattebaaz | +3.29 | 43/56 | #357 | +4.17 | +4.28 | blend |

## Who beats us, whom we beat (nairobi #495 against each team's newest entry)

Beat us: Godtier#465 -1.92, Cyberpsycho#316 -1.86, Happy Happy#496 -1.59, Techy Traders#488 -1.24, Imposters#457 -1.14, Quants Treasure#480 -1.03, Chill Chips#493 -0.86, KRYPTEX#490 -0.44, Team How#500 -0.34, Trade Transmitters#371 -0.14.

We beat 54 of 64; biggest: House · reader#2 +31.04, House · sharp#3 +29.02, Alpha Predators#492 +24.22, OptiMystics#430 +10.64, Hidden Alpha#404 +10.59, Dalal Street#444 +10.33, House · naive#1 +9.87, Apex Syndicate#294 +9.48, Void Stalkers#195 +8.38, Outliers#468 +8.31.

## Who beats the top teams (newest vs newest)

- Imposters: nobody
- Genz7: Imposters -2.84, Cyberpsycho -1.36, TeenPatti -1.01, AJ_The_Trader -0.96, Chill Chips -0.73, Alpha Rodeo -0.59
- TeenPatti: Double Dividend -3.49, Cyberpsycho -0.78, Hidden Alpha -0.54, Imposters -0.21, Alpha Rodeo -0.21
- Alpha Rodeo: Godtier -1.92, Cyberpsycho -1.86, Happy Happy -1.59, Imposters -1.14, Quants Treasure -1.03, Chill Chips -0.86, Team How -0.34, Trade Transmitters -0.14
- MNC Traders: Imposters -3.67, TeenPatti -3.17, Cyberpsycho -2.12, Sattebaaz -1.75, AJ_The_Trader -1.75, PaperHands -1.57, Chill Chips -1.41, Alpha Rodeo -1.26, Techy Traders -1.09, Genz7 -1.03, QuantXAlpha -0.89, HAN SOLO -0.84, The Risk Violators -0.59
- PaperHands: Trinomial -1.25, Imposters -0.91, Genz7 -0.69, Alpha Rodeo -0.58, Pokemons -0.09, TeenPatti -0.06
- AJ_The_Trader: Alpha Rodeo -3.21, Sattebaaz -2.82, Imposters -2.09, TeenPatti -1.88, The Risk Violators -1.43, QuantXAlpha -1.18, HAN SOLO -0.81, Pokemons -0.73, PaperHands -0.63, Chill Chips -0.37
- HAN SOLO: TeenPatti -2.83, Imposters -2.61, Alpha Rodeo -1.96, Pokemons -1.31, Genz7 -1.10, Chill Chips -0.85, PaperHands -0.66, Quantumlesssss -0.04

## Styles (from replays)

Every fight page shows the same deal 1 (hands 3 4 J 9 5 = 32 and 2 10 Q 8 8 = 40, board J 2 Q Q 10), so a team is
seen with two hands only, against many opponents. What the replays show:

- **Followers / nudgers** (quote = the opponent's last quote, carried for board cards, +- a small step): Happy Happy #463
  (exactly ours + 1.1, takes only at 5+ points of edge, ignores absurd prices), PaperHands (round 1: ours + 2.15, sd 0.13),
  Techy Traders (ours - 1.3; first quote with a low hand 5.3 ABOVE its fair), Imposters (ours + 1.3; always swaps in round 4;
  answers exactly 1 lot in round 1), MNC (ours - 1.1), AnalysisParalysis, TeenPatti, Quants Treasure. Their quotes show
  nothing of their hand; they make money by taking. Top teams are of this kind.
- **Readers** (their quote moves with what our quote implies, trust ~1): Hidden Alpha, Apex, Phantom Halo, house reader / sharp.
- **Honest naive-formula quoters** (first quote exactly the naive card count, 103.74 on deal 1): Pravichayah, Quant Qods,
  Chanakya, Apex, Hidden Alpha, Phantom Halo, house bots. We beat these by +5 to +11.
- **Swaps:** top teams swap late (Imposters r4 in 156/159 plays, PaperHands / Techy r5) and account for the opponent's
  discard (fitted swap accounting 0.5-0.9: a discarded 2 raises their price ~5). We used to swap in round 1, which gave
  that information away early (fixed in rio).
- **Answers:** most fitted teams take only at 4-7 points of edge; Imposters / MNC / alpha answer 1 lot in round 1 (61-76%).

## Field model (heist/opp/, heist/data/field.json)

One parameterised bot (heist/opp_core.py) fitted to each team's replays (heist/fit_opp.py: quote error, answer and move agreement), then checked against the live scores of our own files (heist/calib.py). Only imitations within 1.5 of every live score are used; each is weighted by how many live teams share its style. House bots are included as themselves (exact).

| Imitation | Style | Weight | Replay fit (quote err / answer miss / move miss) | Live vs local (our files) |
|---|---|---|---|---|
| Alpha Hunters | blend | 3.0 | 0.60 / 0.34 / 0.04 | #452 +3.64/+2.38; #459 +3.56/+2.43; #466 +3.56/+2.43 |
| IITBHUAVENGERS | blend | 3.0 | 1.25 / 0.17 / 0.07 | #452 +2.76/+3.41; #459 +2.69/+3.09; #466 +2.69/+3.09 |
| THUGS OF BHU | blend | 3.0 | 0.51 / 0.07 / 0.06 | #452 +2.87/+1.92; #459 +2.62/+2.13; #466 +2.62/+2.13 |
| TeenPatti | blend | 3.0 | 1.40 / 0.39 / 0.01 | #452 -1.06/-0.13; #459 +0.14/-0.31; #466 +0.21/-0.31 |
| Double Dividend | follower | 1.875 | 1.74 / 0.24 / 0.04 | #452 +2.51/+3.37; #459 +2.41/+3.80; #466 +2.41/+3.80 |
| Genz7 | follower | 1.875 | 2.56 / 0.32 / 0.02 | #452 -0.29/+0.73; #459 +0.59/+1.07; #466 +0.59/+1.07 |
| Happy Happy #463 | follower | 1.0 | 0.49 / 0.04 / 0.18 | #486 +1.60/+5.05; #495 +1.97/+3.94 |
| PaperHands | follower | 1.875 | 1.76 / 0.22 / 0.01 | #486 +0.56/+1.08; #495 +0.58/+1.84 |
| Pokemons | follower | 1.875 | 1.43 / 0.12 / 0.03 | #452 +0.81/+0.22; #459 +1.18/+0.07; #466 +1.18/+0.07 |
| QuantXAlpha | follower | 1.875 | 2.26 / 0.29 / 0.04 | #459 +0.24/+0.85; #466 +0.24/+0.85; #486 -0.23/+0.14 |
| Quantumlesssss | follower | 1.875 | 1.76 / 0.21 / 0.01 | #486 +2.11/+2.76; #495 +2.70/+3.11 |
| Techy Traders | follower | 1.875 | 2.06 / 0.22 / 0.04 | #486 -2.06/-1.34; #495 -1.24/-0.78 |
| ThunderX | follower | 1.875 | 1.94 / 0.28 / 0.18 | #452 +4.09/+3.37; #459 +3.25/+2.81; #466 +3.25/+2.81 |
| Godtier | honest | 2.75 | 0.78 / 0.03 / 0.11 | #466 -1.92/-2.58; #486 -1.57/-2.54; #495 -1.92/-2.58 |
| HAN SOLO | honest | 2.75 | 1.14 / 0.28 / 0.04 | #452 +2.00/+2.30; #459 +1.96/+2.97; #466 +1.96/+2.97 |
| QUANTSTATIC | honest | 2.75 | 0.53 / 0.09 / 0.09 | #452 +6.79/+5.89; #459 +6.69/+5.85; #466 +6.69/+5.85 |
| Quant Qods | honest | 2.75 | 0.29 / 0.01 / 0.15 | #452 +4.88/+5.33; #459 +4.73/+5.27; #466 +4.73/+5.27 |
| Apex Syndicate | reader | 1.6 | 1.89 / 0.31 / 0.01 | #452 +9.36/+9.40; #459 +8.53/+9.29; #466 +9.49/+9.29 |
| Bulls Squad | reader | 1.6 | 1.39 / 0.23 / 0.03 | #452 +7.65/+8.11; #459 +7.35/+7.82; #466 +7.35/+7.82 |
| Money Heist | reader | 1.6 | 2.05 / 0.38 / 0.07 | #452 +4.71/+3.61; #459 +4.62/+3.38; #466 +4.62/+3.38 |
| Phantom Halo | reader | 1.6 | 2.36 / 0.19 / 0.29 | #466 +1.01/+1.64; #486 +1.21/+1.51; #495 +1.01/+1.64 |
| QUANTUMLYSTUPID | reader | 1.6 | 0.38 / 0.10 / 0.04 | #486 +2.73/+3.51; #495 +2.50/+3.33 |

Not calibrated (left out): AJ_The_Trader, AnalysisParalysis, Balls of Wall Street, Bayes and Bulls, Blind_Ambition, Chanakya, Cyberpsycho, Dalal Street, Dark Pool Divers, Deal & Steal, Explorers, Happy Happy, Hidden Alpha, Imposters, MNC Traders, OptiMystics, Outliers, Pravichayah, Quants Treasure, Sattebaaz, Specter, The Risk Violators, Trade Transmitters, Void Stalkers, alpha.

