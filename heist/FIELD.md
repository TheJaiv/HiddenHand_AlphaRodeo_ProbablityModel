# The live field (heist/FIELD.md)

Census 2026-10-08 15:18 from the public standings and fight list (heist/census.py; data in heist/data/). Every live fight uses the same hidden 400-deal set, so a deterministic bot scores exactly the same against an unchanged opponent upload: our paired live comparisons have no deal noise per opponent.

Our entries: #486 tokyo, #495 nairobi, #505 rio, #513 moscow, #561 helsinki, #565 lisbon, #569 j01 (safe-quote test), #573 e01.

## Top 15

| # | Team | Score | Won | Newest | e01 #573 vs it | helsinki #561 vs it | Style (fit) |
|---|---|---|---|---|---|---|---|
| 1 | PaperHands | +5.59 | 54/56 | #508 | -0.44 | -0.32 | blend |
| 2 | Imposters | +5.34 | 55/56 | #574 | +0.14 | - | blend |
| 3 | Alpha Rodeo | +5.01 | 53/56 | #573 | - | - | - |
| 4 | Genz7 | +4.64 | 50/56 | #262 | -0.71 | -1.29 | follower |
| 5 | QuantXAlpha | +4.62 | 52/57 | #547 | -0.10 | -0.06 | follower |
| 6 | TeenPatti | +4.40 | 50/56 | #330 | +1.26 | +0.69 | blend |
| 7 | MNC Traders | +3.88 | 36/56 | #581 | +0.67 | - | blend |
| 8 | HAN SOLO | +3.85 | 48/56 | #563 | +0.21 | -0.69 | blend |
| 9 | Techy Traders | +3.70 | 42/56 | #570 | +3.41 | - | follower |
| 10 | Chill Chips | +3.36 | 51/56 | #531 | +0.23 | +0.98 | blend |
| 11 | Happy Happy | +3.36 | 47/56 | #575 | +0.26 | - | blend |
| 12 | Pokemons | +3.33 | 43/57 | #214 | +0.42 | +0.68 | follower |
| 13 | The Risk Violators | +3.23 | 44/56 | #391 | +1.42 | +1.79 | blend |
| 14 | Quants Treasure | +3.07 | 44/57 | #514 | +0.27 | +0.01 | follower |
| 15 | Double Dividend | +2.94 | 41/57 | #453 | +2.06 | +0.44 | follower |

## Who beats us, whom we beat (e01 #573 against each team's newest entry)

Beat us: Genz7#262 -0.71, PaperHands#508 -0.44, QuantXAlpha#547 -0.10.

We beat 61 of 64; biggest: House · reader#2 +31.47, House · sharp#3 +30.42, Alpha Predators#577 +22.53, Alpha Predators#492 +22.53, OptiMystics#430 +12.59, Chanakya#200 +9.77, IITBHUAVENGERS#527 +9.68, Code Riders#533 +9.58, Apex Syndicate#294 +9.36, Void Stalkers#195 +9.34.

## Who beats the top teams (newest vs newest)

- PaperHands: Chill Chips -1.49, Imposters -1.31
- Imposters: Alpha Rodeo -0.14
- Alpha Rodeo: Genz7 -0.71, PaperHands -0.44, QuantXAlpha -0.10
- Genz7: Imposters -2.82, AJ_The_Trader -1.58, Cyberpsycho -1.36, QuantXAlpha -1.16, TeenPatti -1.01, PaperHands -0.85, Chill Chips -0.74
- QuantXAlpha: PaperHands -3.14, Imposters -1.46, Chill Chips -0.50, Sattebaaz -0.31, The Risk Violators -0.19, AJ_The_Trader -0.07
- TeenPatti: Double Dividend -3.49, PaperHands -1.68, Alpha Rodeo -1.26, Cyberpsycho -0.78, QuantXAlpha -0.39, Imposters -0.21
- MNC Traders: Outliers -5.12, PaperHands -4.94, Imposters -4.42, QuantXAlpha -3.67, TeenPatti -3.25, Techy Traders -2.74, QUANTUMLYSTUPID -2.54, Cyberpsycho -2.53, AJ_The_Trader -2.11, Happy Happy -2.10, Hidden Alpha -2.03, Genz7 -1.41, Sattebaaz -1.35, Quantumlesssss -1.16, HAN SOLO -1.05, Alpha Rodeo -0.72, Quants Treasure -0.72, The Risk Violators -0.58, Chill Chips -0.33, ThunderX -0.30, Pokemons -0.10
- HAN SOLO: PaperHands -3.95, TeenPatti -2.36, Imposters -2.03, Genz7 -1.46, QuantXAlpha -1.26, Pokemons -0.79, Chill Chips -0.46, Alpha Rodeo -0.21, AJ_The_Trader -0.04

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

## Afternoon findings (live)

- **Extraction gap.** Against the mid-field the top teams make far more PnL per deal than we do (ThunderX: PaperHands +23.4,
  Imposters +17.9, us +1.3; Pokemons +26.0 / +11.1 / +3.3; MNC +23.2 / +12.8 / +6.6; Blind_Ambition +29.7 / +19.1 / +7.5;
  Double Dividend +24.6 / +13.2 / +4.2). On the same opponents the top three beat our current versions by +0.4 to +0.6.
- **Hand effect** (heist/handeffect.py; replays show both hands): quote slope per point of own hand ~0.85-1.0 for honest
  quoters (naive, QUANTSTATIC, Bulls, Apex, Blind, alpha, Void), ~0 for hiders / followers (Sattebaaz, Risk Violators,
  Pokemons, Godtier), negative for MNC / TeenPatti / Genz7 (-0.4), Cyberpsycho, Imposters (-0.25). Deal 1 always pairs a 32
  hand with a 40 hand, so reading the opponent and hiding one's own hand look alike here.
- **Pickers.** The refreshed ThunderX imitation (matches live) shows how followers that read us and take only at ~5 points of
  edge beat us: our maker PnL is negative in every round (-8.7 per play) while our taking wins (+14).
- **Peekers.** Quants Treasure peeks in rounds 1-3 (9 points a deal). A defence (safe quotes + taker margin after 2 peeks)
  made it worse live (lisbon: QT -0.65, Team How -1.4).
- **Plateau.** rio, moscow, helsinki, lisbon and e01 all score the same live (+5.3) but split opponents differently
  (helsinki-line: Godtier +2.5, Cyberpsycho +1.9, Chanakya +3.5; rio: Imposters +0.8, Genz7 +0.6, PaperHands +0.4).

## Field model (heist/opp/, heist/data/field2.json)

One parameterised bot (heist/opp_core.py) fitted to each team's replays (heist/fit_opp.py: quote error, answer and move agreement), then checked against the live scores of our own files (heist/calib.py). Only imitations within 1.5 of every live score are used; each is weighted by how many live teams share its style. House bots are included as themselves (exact).

| Imitation | Style | Weight | Replay fit (quote err / answer miss / move miss) | Live vs local (our files) |
|---|---|---|---|---|
| Alpha Hunters | blend | 3.429 | 0.60 / 0.34 / 0.04 | #452 +3.64/+2.38; #459 +3.56/+2.43; #466 +3.56/+2.43 |
| Code Riders | blend | 3.429 | 1.66 / 0.29 / 0.00 | #513 +9.54/+9.51; #561 +10.09/+10.58; #565 +12.53/+10.98 |
| Deal & Steal | blend | 3.429 | 0.71 / 0.07 / 0.01 | #452 +3.52/+3.72; #459 +3.75/+3.72; #466 +3.76/+3.72 |
| Outliers | blend | 3.429 | 3.65 / 0.27 / 0.03 | #513 +4.17/+4.80; #561 +3.68/+3.71; #565 +3.38/+2.66 |
| QUANTUMLYSTUPID | blend | 3.429 | 1.14 / 0.15 / 0.03 | #565 +7.79/+8.35; #569 +4.57/+5.70; #573 +6.07/+6.04 |
| THUGS OF BHU | blend | 3.429 | 0.51 / 0.07 / 0.06 | #452 +2.87/+1.92; #459 +2.62/+2.13; #466 +2.62/+2.13 |
| ThunderX | blend | 3.429 | 2.43 / 0.31 / 0.20 | #513 +3.75/+2.02; #561 +1.95/+1.19; #565 -0.16/+1.12 |
| IITBHUAVENGERS | follower | 7.0 | 1.70 / 0.22 / 0.04 | #513 +9.63/+10.98; #561 +11.09/+11.62; #565 +11.48/+12.24 |
| Pravichayah | follower | 7.0 | 1.23 / 0.24 / 0.00 | #452 +1.84/-0.05; #459 +1.94/+0.11; #466 +1.94/+0.11 |
| Godtier | honest | 2.0 | 0.78 / 0.03 / 0.11 | #466 -1.92/-2.58; #486 -1.57/-2.54; #495 -1.92/-2.58 |
| Money Heist | honest | 2.0 | 1.52 / 0.44 / 0.05 | #513 +5.94/+6.03; #561 +5.22/+6.33; #565 +4.20/+6.01 |
| QUANTSTATIC | honest | 2.0 | 0.53 / 0.09 / 0.09 | #452 +6.79/+5.89; #459 +6.69/+5.85; #466 +6.69/+5.85 |
| Quant Qods | honest | 2.0 | 0.29 / 0.01 / 0.15 | #452 +4.88/+5.33; #459 +4.73/+5.27; #466 +4.73/+5.27 |
| Specter | honest | 2.0 | 0.57 / 0.09 / 0.39 | #513 +5.74/+6.43; #561 +6.01/+7.04; #565 +5.59/+7.22 |
| TEAM ERROr | honest | 2.0 | 3.11 / 0.15 / 0.00 | #513 +7.05/+5.22; #561 +6.03/+5.36; #565 +5.31/+4.57 |
| Apex Syndicate | reader | 4.0 | 1.89 / 0.31 / 0.01 | #452 +9.36/+9.40; #459 +8.53/+9.29; #466 +9.49/+9.29 |

Not calibrated (left out): AJ_The_Trader, ASYMMETRIC EDGE, Algo X, Alpha Predators, AnalysisParalysis, Apex Syndicate, Balls of Wall Street, Bayes and Bulls, Blind_Ambition, Bulls Squad, Chanakya, Chill Chips, Code Riders, Cyberpsycho, Dalal Street, Dark Pool Divers, Deal & Steal, Double Dividend, Explorers, Genz7, HAN SOLO, Happy Happy, Hidden Alpha, Imposters, MNC Traders, Money Heist, OptiMystics, Outliers, PaperHands, Phantom Halo, Pokemons, Pravichayah, QuantXAlpha, Quants Treasure, Quantumlesssss, Sattebaaz, Specter, TEAM ERROr, Team How, Techy Traders, TeenPatti, The Risk Violators, ThunderX, Trade Transmitters, Trinomial, Void Stalkers, alpha.

