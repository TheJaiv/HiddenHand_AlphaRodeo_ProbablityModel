# Upload plan

Every file in this folder already has our header (Alpha Rodeo / Jaiv Patel / Arpit Gupta) and passes
`python backtester.py --validate`. The arena allows one upload every 10 minutes, and the newest
working file is our entry, so the LAST upload must be the bot we want judged.

## Order

| # | File | When | Leave it up | What it tells us |
|---|---|---|---|---|
| 0 | `zoo/liar.py` | done | until #1 | which teams believe our quotes |
| 1 | `01_hider.py` | Wed, now | 30 min | which teams depend on reading our quotes |
| 2 | `02_noisy_sharp.py` | Wed | 30 min | which teams identify hands exactly from quotes (rival_1 style) |
| 3 | `03_old_plan.py` | Wed | 30 min | how a careful sharp-based bot does in the real field |
| 3d | `03d_bridge_7.py` | Wed evening | 20 min | a mid-strong team (pool about +7) |
| 3e | `03e_bridge_9.py` | Wed evening | 20 min | a strong field-farmer (pool about +9, very strong vs ai-style and hider teams) |
| 3f | `03g_bridge_11_strong.py` | Wed evening | 30 min | candidate base: beats rival_1 and rival_3 locally; see how it does live |
| 4 | `04_rival_1.py` | Wed evening | 45 min | real-field result of strong bot A |
| 5 | `05_rival_3.py` | Wed evening (optional) | 45 min | real-field result of strong bot C |
| 6 | `06_rival_2.py` (or our rival_2 + B1) | Wed night | overnight | real-field result of strong bot B, the likely base |
| 7 | `04_rival_1.py` again | Thu morning | 45 min | rival_1 against the SAME field as #6, for gate G |
| 8+ | `moneyheist_bot.py` versions | Thu afternoon | - | improved chosen base |
| last | `moneyheist_bot.py` final | deadline - 1 h | - | the entry that is judged |

Why this order: cheap probes first (they only teach us about the field), strong bots later (their
replays are public, so other teams see their tricks as late as possible), and #6 and #7 close together
so rival_1 and rival_2 are compared against the same field.

Optional probes, only if there is spare time: `03a_mid_steer.py` (huge wins only against quote-readers), `03b_mid_guard.py`, `03c_mid_bayes.py`, `03f_bridge_11.py`. They score below old_plan or close to 03g, so they teach less.

## What to record after each upload (PROBES.md)

For every team in the standings: our score in the fight against them. Also the house sharp's score
against them, if the arena shows house-bot fights. Open 2-3 replays and write one line on how they quote.

## Reading the results: fingerprints

Our probe's score against each known opponent type, measured locally (300 deals, seed 1):

| Opponent type | vs house sharp | vs liar | vs hider | vs noisy_sharp |
|---|---|---|---|---|
| reader-like (honest, reads quotes) | +4 | **+8.7** | +5.8 | +4 |
| old_plan-like (careful team) | -8 | -6 | **-3** | -8 |
| rival_1-like (exact identification) | -21 | -14 | -11 | **-11** (half of sharp's loss) |
| rival_2-like (Bayesian, many hypotheses) | -21 | -14 | **-5** | -21 |
| rival_3-like (exact models + look-ahead) | -20 | **-21** | -11 | -17 |

How to use it:
- A team that loses badly to **liar** believes quotes: a reader-type bot, easy to farm.
- A team that beats sharp by a lot but beats **noisy_sharp** only by half is **rival_1-like**.
- A team that beats sharp by a lot but barely beats **hider** is **rival_2-like**.
- A team that crushes **liar** as hard as sharp is **rival_3-like**.
- Count the types. Many reader/average teams: the field favours rival_2. Several rival-like teams near
  the top: the field favours rival_1. This is the live evidence for gate G.
