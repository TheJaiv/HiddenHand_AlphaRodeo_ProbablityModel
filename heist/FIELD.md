# The live field (heist/FIELD.md)

Census 2026-10-08 16:21 from the public standings and fight list (heist/census.py; data in heist/data/). Every live fight uses the same hidden 400-deal set, so a deterministic bot scores exactly the same against an unchanged opponent upload: our paired live comparisons have no deal noise per opponent.

Our entries: #486 tokyo, #495 nairobi, #505 rio, #513 moscow, #561 helsinki, #565 lisbon, #569 j01 (safe-quote test), #573 e01, #586 stockholm, #588 30% nudge, #591 palermo, #596 aa01. Since 15:40 the house bots no longer count.

## Top 15

| # | Team | Score | Won | Newest | palermo #591 vs it | 30% nudge #588 vs it | Style (fit) |
|---|---|---|---|---|---|---|---|
| 1 | Imposters | +5.01 | 53/54 | #574 | +1.91 | -0.48 | blend |
| 2 | PaperHands | +4.67 | 50/53 | #508 | -1.60 | -1.73 | blend |
| 3 | TeenPatti | +4.05 | 48/54 | #330 | +2.77 | +1.93 | blend |
| 4 | Genz7 | +3.97 | 45/54 | #262 | -1.04 | -0.54 | follower |
| 5 | QuantXAlpha | +3.95 | 48/53 | #547 | +1.86 | -0.28 | follower |
| 6 | AJ_The_Trader | +3.47 | 45/54 | #585 | +0.74 | -0.95 | blend |
| 7 | MNC Traders | +3.34 | 32/44 | #594 | - | - | blend |
| 8 | Alpha Rodeo | +3.21 | 41/44 | #596 | - | - | - |
| 9 | HAN SOLO | +3.18 | 43/53 | #563 | -1.67 | +0.99 | blend |
| 10 | Chill Chips | +2.94 | 49/54 | #531 | +1.18 | +1.74 | blend |
| 11 | The Risk Violators | +2.84 | 40/54 | #391 | +3.03 | +2.65 | blend |
| 12 | Pokemons | +2.69 | 40/55 | #214 | +4.48 | +0.88 | follower |
| 13 | Happy Happy | +2.60 | 45/55 | #575 | +2.07 | +2.07 | blend |
| 14 | Techy Traders | +2.54 | 7/8 | #599 | - | - | follower |
| 15 | Double Dividend | +2.45 | 38/54 | #453 | +4.00 | +2.11 | follower |

## Who beats us, whom we beat (palermo #591 against each team's newest entry it played)

Beat us: HAN SOLO#563 -1.67, PaperHands#508 -1.60, Genz7#262 -1.04, Techy Traders#589 -0.34.

We beat 52 of 56; biggest: OptiMystics#430 +17.55, Code Riders#533 +14.13, IITBHUAVENGERS#527 +12.16, Alpha Predators#590 +11.50, Dalal Street#572 +11.20, Apex Syndicate#294 +10.45, Bulls Squad#370 +10.25, Void Stalkers#195 +9.10, Chanakya#200 +8.69, AnalysisParalysis#242 +8.55.

## Who beats the top teams (newest vs newest)

- Imposters: Alpha Rodeo -0.92
- PaperHands: Chill Chips -1.49, Imposters -1.31, Alpha Rodeo -0.49
- TeenPatti: Double Dividend -3.49, PaperHands -1.68, Cyberpsycho -0.78, Alpha Rodeo -0.75, QuantXAlpha -0.39, Imposters -0.21
- Genz7: Imposters -2.82, Techy Traders -2.28, AJ_The_Trader -1.63, Cyberpsycho -1.36, QuantXAlpha -1.16, TeenPatti -1.01, PaperHands -0.85, Chill Chips -0.74, MNC Traders -0.71
- QuantXAlpha: PaperHands -3.14, Imposters -1.46, Chill Chips -0.50, The Risk Violators -0.19, AJ_The_Trader -0.12
- AJ_The_Trader: PaperHands -2.31, Alpha Rodeo -2.12, Sattebaaz -1.65, Imposters -1.25, TeenPatti -0.82, The Risk Violators -0.79, Pokemons -0.67, MNC Traders -0.04, Chill Chips -0.00
- MNC Traders: PaperHands -4.19, Imposters -3.07, QUANTUMLYSTUPID -2.56, Happy Happy -1.67, Cyberpsycho -1.49, QuantXAlpha -1.04, Chill Chips -0.97, Quantumlesssss -0.88, TeenPatti -0.35, Alpha Rodeo -0.22, Outliers -0.06, AJ_The_Trader -0.02
- Alpha Rodeo: QuantXAlpha -0.97, Genz7 -0.92, Cyberpsycho -0.71

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

