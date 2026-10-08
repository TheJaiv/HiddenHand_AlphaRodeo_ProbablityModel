# Hunt ledger (Thu 8 Oct)

Parent: zoo/rival_2.py (live #129: +4.94 mean over 85 fights; live #368: +2.39 over 37 on Thursday's field).

## Why the live gap (live fights, paired on the same opponent uploads, tools/live_ab.py)

| Upload | File (identified from replays) | vs rival_2 #368, shared opponents |
|---|---|---|
| #328 | attack line (attack_v05) | -0.84 +-1.18 (n=10): worst vs AnalysisParalysis, Imposters, Pokemons, Techy Traders |
| #343 | merge_v07 line | +0.78 +-1.09 (n=13): better vs Happy Happy, Risk Violators, MNC, AJ, Genz7; worse vs Pokemons, Imposters, Techy Traders |
| #351 | rival_1 | -1.36 (n=24) |

Neither attack nor merge is significantly different from rival_2 live. What the replays of the strong teams show
(zoo/arena_raw/, 11 teams refitted): 10 of 11 learn from our TRADES on their quotes (switching that off
in their imitation costs 7-24 points of response agreement), 7 of 11 barely read our QUOTES. Steering quotes
only pay against readers.

## Test pool and rule

naive, reader, sharp, rival_1, rival_2, arena_imposters, arena_pokemons, arena_sattebaaz, arena_quants_treasure,
arena_outliers; 400 deals; accepted only if the gain over rival_2 is above 2 standard errors on seeds 5 6 AND 7 8,
and it does not lose to rival_2 head to head. Calibration caveat: of the imitations, only Imposters, Pokemons and
Outliers are within ~1.5 of rival_2's live score against that team; the TeenPatti/Genz7/AJ/PaperHands imitations
still lose to rival_2 locally although those teams beat it live, so they are left out. Confirm every version live
with tools/live_ab.py before trusting it.

## Versions

| Version | Change (one at a time from its parent) | Pool vs rival_2 (5 6 / 7 8) | Head to head vs rival_2 | Costs | Speed |
|---|---|---|---|---|---|
| hunt_v01 | P_NAIVE 0.3 -> 0.6 and TAU_PRIOR (0, .6) (1.5, .25) (3, .15) | +1.08 / +1.05 (+-0.16) | +4.07 / +4.05 | reader -1.9, sharp -1.3, Quants Treasure -1.2 | 1.9 ms |
| hunt_v02 | hunt_v01 with TAU_PRIOR (0, .4) (1.5, .35) (3, .25) | +1.56 / +1.59 (+-0.20) | +3.49 / +4.08 | reader -3.3/-3.6, Quants Treasure -1.9 | 0.6 ms |

Without the two rival_* opponents, hunt_v01's gain on seeds 7 8 is +0.31 (house bots 3 of 8 there; weighted like the
live field, about 3 house bots in 45, it is about +1.0).

## Live results

| Upload | File | vs rival_2 #368 on shared opponent uploads (tools/live_ab.py) |
|---|---|---|
| #383 | hunt_v01 | +1.34 +-0.97 (n=19, 01:48). Big gains vs AJ (+5.7), HAN SOLO (+4.7), Happy Happy (+3.7), Imposters (+2.9), Genz7 (+2.6). Still loses to Quants Treasure (-3.06), TeenPatti (-1.71), Cyberpsycho (-1.64), PaperHands (-0.62), Genz7 (-0.31) |

## Tried and rejected

| Idea | Result vs rival_2 |
|---|---|
| P_NAIVE 0.6 alone (c1) | +0.54 / +0.50: passes, but hunt_v01 is better |
| TAU_PRIOR heavier alone (c2) | +0.47 / +0.30: passes, but hunt_v01 is better |
| Trade learning also for non-honest quoters (remove the lam < 1 skip) (c3) | +0.05: no effect |
| More weight on "their quotes say nothing" (LAM_PRIOR) (c4) | +0.43, but -0.84 vs Pokemons |
| P_NAIVE 0.75 with hunt_v01's tau (c6) | +0.71 / +0.59: worse than hunt_v01, reader -3.9 |
| Trade bait: trade 1-2 lots against our own hand in rounds 1-2 | about 0 overall: helps vs TeenPatti/Imposters/Sattebaaz/rival_1 imitations, hurts vs PaperHands/Pokemons/Genz7/readers |
| Cap our quote at 4 / 6 / 9 from our own value (except the free side at the position limit) | -2.9 / -1.8 / -0.8 vs hunt_v01 (seeds 5 6): the off-fair quotes pay on average; the one-deal replays misled |
| Ignore an opponent quote that equals our last quote (mirror detector) | -0.06 overall, -0.75 vs the Quants Treasure imitation |
| Swap later (SWAP_TH 30/20/12/6/4 and 60/40/20/8/4) | -0.12 / -0.18 and -0.39 / -0.53 vs hunt_v01: better vs readers and rivals, worse vs every arena imitation |

## 07:30 check (main session)

- hunt_v02 live (#393) vs hunt_v01 (#383): -0.38 +-0.76 on 40 shared opponent uploads (100 fights). Not better; the referee
  agent's split shows v02 loses to the teams we have no imitation of (about 70% of the field) the way it loses to readers.
- Field-mix pool (12 reader-family zoo bots + 7 arena imitations) reproduces "v02 below v01" (-0.21) but NOT "rival_2 below
  v01" (+0.20 there, about -1.0 live). No single reader/imitation mix fits both, so local pools only help together with live A/B.
- hunt_v10 (strategist agent, parent hunt_v01): adds "blend quoter" hypotheses to the opponent model (their quote = blend of
  their own fair and OUR last quote, carried for board cards; responses on their own fair; a skew with our position).
  Field-mix pool seeds 9 10: +0.21 vs hunt_v01; 25-opponent pool (field mix + rival_1/2 + genz7/aj/kryptex/quantumlesssss
  imitations) seeds 11 12: +0.16. Gains: outliers +2.1/+2.3, aj +1.07, quants_treasure +0.6/+1.0, paperhands_v5 +0.3/+0.8,
  hider +0.4; costs about -0.1 vs reader-family bots. Validate OK, 0.33 ms max. Next live A/B candidate.

## Strategist agent (round 2)

Parent hunt_v10. Pool = the 25 opponents of the round-2 protocol (first 12 = reader family), 400 deals, cached
runner versions/hunt_scratch_B/ceval.py (same seeding as tools/eval.py, --procs 4). Diffs are candidate - hunt_v10,
+- = 2 standard errors. Noise floor: an identical copy of hunt_v10 gives -0.014 +-0.012 (mid_guard uses an unseeded RNG).
Baseline hunt_v10: pool +8.02 (seeds 5 6), +7.70 (7 8); H2H vs hunt_v01 -0.04 (5 6), -0.20 (7 8), both +-0.30.

Field facts (versions/hunt_scratch_B/field_fit.py on zoo/arena_raw, current entries): regressing each team's quote minus
its naive fair on (what our last quote implies, its own hand, its position, lots we bought on its quotes):
house reader/sharp b1 0.80 b2 0 resid 0; ~15 teams quote naive-like (b1 ~ 0); ~20 teams blend/hide (b1 0.3-0.9,
b2 -0.6..-1.0, resid 2.5-5) and move their quote +0.6..+1.9 per lot we buy on their quotes (trade learning). The
arena imitations reproduce that archetype; the zoo reader family does not (resid 0, b2 0).

| Variant (scratch B) | Change | Pool diff 5 6 | Reader fam. | Others | H2H vs v10 | Verdict |
|---|---|---|---|---|---|---|
| (scratch A) b1_th | taker-threshold hypotheses incl. planning | -0.54 +-0.15 (old 12-pool) | | | | rejected |
| (scratch A) c1_hyb | hybrid reader-blend hypotheses | -0.14 +-0.06 (old 12-pool) | | | | rejected |
| b01_open | a round-1 quote of exactly 105.00 is 80% uninformative | -0.000 +-0.024 | +0.04 | -0.04 | +0.01 | rejected: no effect (hider +0.49, QT -0.42) |
| b02_sigq1 | SIG_Q 0.5 -> 1.0 | +0.046 +-0.069 | -0.06 | +0.14 | +0.68 +-0.46 | rejected: not significant; readers -0.4..-0.5 each |
| b03_sigr2 | SIG_R 1.0 -> 2.0 | -0.036 +-0.064 | -0.17 | +0.09 | +0.23 | rejected |
| b04_risk40 | RISK 60 -> 40 | +0.006 +-0.025 | 0.00 | +0.01 | -0.03 | rejected: flat |
| b05_risk100 | RISK 60 -> 100 | +0.022 +-0.029 | +0.02 | +0.02 | -0.08 | rejected: flat |
| b06_lam02 | add lam 0.2 hypotheses (mass from lam 0) | -0.113 +-0.069 | -0.23 | -0.01 | -0.05 | rejected |
| b08_sigqh | per-hypothesis quote noise sd 0.5 / 2.0 | -0.357 +-0.109 | -0.51 | -0.22 | +1.31 +-0.53 | rejected |
| b09_sigrh | per-hypothesis response noise sd 1.0 / 2.5 | -0.590 +-0.115 | -0.70 | -0.49 | +1.18 +-0.52 | rejected |
| b07_blam02 -> **hunt_v11** | blend hypotheses also with lam 0.2 (BLEND_LAM (1 .5, .7 .2, .4 .15, .2 .15)) | +0.083 +-0.038; 7 8: +0.123 +-0.039 | +0.05 / +0.08 | +0.11 / +0.16 | +0.34 +-0.27 / +0.57 +-0.26 (vs v01 +0.23 / +0.36) | ACCEPTED (hider +0.9/+0.8, outliers +0.45/+0.43, aj +0.36/+0.43, genz7 +0.35/+0.12, quantumlesssss +0.20/+0.25; QT -0.40/-0.16, mid_bayes -0.23/-0.16) |
| b10_thinf | taker-threshold hypotheses (0 / 2) in inference only | -0.417 +-0.106 | -0.47 | -0.37 | +1.18 | rejected |
| b11_btau (on v10) | blend-only TAU prior (0 .3, 1.5 .4, 3 .3) | +0.183 +-0.046 | -0.02 | +0.37 | +0.11 | superseded by b17 (same change on hunt_v11) |
| b13_pext6 | P_EXT 0.9 -> 0.6 (crush gate; p_raw tops out ~0.7 vs the house reader because clamp/sane readers look alike until a crush, so the 0/195 crush never fired) | +0.569 +-0.053 | +1.24 (reader +3.4, sharp +2.8, peeker +3.9) | -0.05 (QT +2.6, imposters -0.67, pokemons -0.90) | **-1.26 +-0.27** (vs v01 -1.25) | rejected: false crushes vs planners (our own line), loses H2H |
| b12_crush / b14_crush (on v11) | 0/195 candidates in rounds <= 4 in ANY slot order when p_reader >= 0.97 and p_raw >= 0.6 | +0.176 +-0.040 / +0.174 +-0.040 | +0.67 | -0.28 (QT -1.6..-1.7, pokemons -0.7, genz7 -0.5..-0.6) | -0.39 +-0.18 / -0.41 +-0.18 | rejected: false crushes (2 quotes fit any reader exactly), QT mirror crushed |
| b18 / b19 / b20 (scratch) | crush gate + "reader hypotheses explained their last 1-2 quotes" / "a probe was confirmed" | spot checks only (40 deals) | | | b18 vs v11 -1.24, b19 -0.85 (planner quotes fit a reader with SIG_Q 0.5); b20 never fired | dropped |
| b17_btau -> **hunt_v12** | on hunt_v11: blend quoters learn from our trades more often: blend-only TAU prior (0 .3, 1.5 .4, 3 .3) instead of (0 .6, 1.5 .25, 3 .15) (field replays: blend teams move their quote +0.6..+1.9 per lot we buy) | +0.147 +-0.043; 7 8: +0.138 +-0.041 | -0.025 / -0.038 | +0.31 / +0.30 | vs v11 -0.001 +-0.29 / -0.13 +-0.28 / seeds 9-12 +0.006 +-0.20 (a tie); vs v01 +0.20 / +0.25 / +0.24; vs techy_traders_v10 +1.96 / +1.53 | ACCEPTED (imposters +0.36/+0.53, sattebaaz +0.52/+0.51, outliers +0.41/+0.47, teenpatti +0.42/+0.40, paperhands +0.68/+0.73, kryptex +0.62/+0.41, quantumlesssss +0.38/+0.42, rival_1 +0.35/+0.30; mid_guard -0.42/-0.57 (unseeded RNG), QT -0.18) |
| b21/b22/b23 (scratch, on v11) | exact house-formula reader test (their 3+ quotes fit the reader formula, one trust t, within 0.1) as the crush gate; b21 slot-theirs only (never fired in time), b22 any slot (crushed the QT mirror: a mirror fits t = 1, O = 5*C0/(N+5)), b23 = b22 with 0.5 <= t <= 0.95 | spot checks (40 deals): b23 reader +3.5, sharp +1.0, QT 0, v11 0 | | | | superseded by b24/b26 |
| b24_crushexact (on v12) | b23 on hunt_v12 (EX_TOL 0.1) | +0.132 +-0.022; 7 8: +0.148 +-0.024 | +0.30 / +0.32 | -0.02 / -0.01 | -0.029 +-0.047 / -0.033 +-0.048 | replaced by b26: one false crush of hunt_v12 in 400 deals (3 planner quotes fit the formula within 0.1) |
| b26_crushexact -> **hunt_v13** | b24 with EX_TOL 0.02 (house reader residuals are <= 0.003) | +0.140 +-0.021; 7 8: +0.163 +-0.021 | +0.30 / +0.34 | -0.005 / -0.000 | vs v12 0.000 +-0.000 / -0.013 +-0.026; vs v01 +0.20 / +0.24; vs techy_traders_v10 +1.96 / +1.53 (= v12) | ACCEPTED: reader +3.2/+3.3, sharp +0.95/+1.08, swapper +0.36/+0.37; sharp_t05 -0.52/-0.45, ai_typical -0.24/-0.26; zero effect on every arena imitation. Live: only the house reader and sharp are exact formula readers (field_fit: no team quotes the formula exactly), so expect about +4.2 / 45 = +0.09 on the live average |
| b27_pblend20 (on v13) | P_BLEND 0.12 -> 0.2 | +0.072 +-0.046; 7 8: +0.051 +-0.044; fresh 9 10: +0.031 +-0.044 | -0.01 / -0.02 / -0.06 | +0.15 / +0.12 / +0.11 | +0.39 +-0.32 / -0.00 / +0.00 | rejected: passes 5 6 and 7 8 only marginally, fades on fresh seeds, gains only on imitations (outliers, aj, QT, quantumlesssss) while the reader family drifts down |
| b28_nplan8 (on v13) | plan over the top 8 hypotheses instead of 6 | +0.133 +-0.064; 7 8: +0.011 +-0.065 | +0.12 / +0.01 | +0.15 / +0.01 | +0.43 / -0.21 (+-0.43) | rejected: does not hold on 7 8 (mid_bayes +1.0 both, sharp -0.3 both) |
| b31_swap5 (on v13) | swap more in round 5: SWAP_TH r5 4.0 -> 1.5 | +0.003 +-0.014 | 0.00 | +0.01 | -0.01 | rejected: flat |
| b32_curclamp (on v13) | readers of the price they answer (CUR) clamp its implied hand to 5..65 (a one-deal trace: quoted 140 to a "CUR reader", Pokemons/Imposters sold at 138, V 103) | -0.053 +-0.022 | -0.06 | -0.05 | +0.18 | rejected (ai_typical -0.45, QT -0.52): the one-deal trace misled again |
| b33_crush08 -> **hunt_v14** | crush only exact readers with the house trust 0.8: fitted t within 0.79..0.81 instead of 0.5..0.95 | +0.032 +-0.018; 7 8: +0.034 +-0.017; fresh 9 10: +0.044 +-0.018 | +0.06 / +0.07 / +0.09 | +0.00 / -0.00 / +0.01 | vs v13 0.000 / 0.000 / +0.03; vs v12 0.000 / -0.013 / 0.000 (the seed-10 false crush of v12 is gone); vs v01 +0.20 / +0.24 / +0.35 | ACCEPTED: keeps reader/sharp gains, drops the losing crushes (sharp_t05 +0.52/+0.45/+0.63, ai_typical +0.24/+0.26/+0.23). Why: in the turn order a reader reads the same quote of mine twice, so 3 quotes can fit a planner (t 0.85 seen); live targets are the house reader/sharp (TRUST 0.8, public code) |
