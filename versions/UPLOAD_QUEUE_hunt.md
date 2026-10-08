# Upload queue, hunt line (Thu 8 Oct) - kept by the referee agent

Ranked list of files to upload next. Rule: a file goes ABOVE the current live best only if the evidence
says it is better overall; live paired evidence (tools/live_ab.py, same opponent uploads) beats local
evidence when both exist. Local evidence = tools/eval.py on FRESH seeds 9 10 (the strategist tunes on
5 6 / 7 8), 400 deals, pool: naive reader sharp rival_1 rival_2 + arena imitations (imposters, pokemons,
sattebaaz, quants_treasure, outliers, teenpatti_v4, paperhands_v5), all paired on the same deals.
"EXCL" = the pool without rival_1/rival_2 (our own bots are not in the real field).

Last update: 08:10 (referee 2; the CURRENT queue is the newest '## Update' section at the bottom; everything above is history)

## Queue

| Rank | File | Live paired | Local fresh seeds 9 10 (diff vs hunt_v01, +-2se) | Head to head | Validate / speed / header | Recommendation |
|---|---|---|---|---|---|---|
| 1 | versions/hunt_v01.py (entry #383) | vs rival_2 #368: +0.73 +-0.82 (n=30, 02:16) | - (base) | vs rival_2 +4.36 | OK / 0.40 ms max / OK | Current live best. Keep as the final unless a candidate beats it LIVE. NOTE: the live entry right now is #393 (hunt_v02); re-upload hunt_v01 if nothing better appears |
| 2 | versions/hunt_v02.py (entry #393) | vs hunt_v01 #383: -0.39 +-0.78 (n=39); 0.00 +-0.83 on the 27 opponents common with #368. vs rival_2 #368: +0.85 +-1.45 (n=27) | POOL +0.86 +-0.17, EXCL +0.82 +-0.18; but reader -1.39, sharp -1.84, naive -0.28, rival_2 -0.95 | vs hunt_v01 +1.40, vs rival_2 +3.41 | OK / 0.39 ms max / OK | Not above hunt_v01: local gain does not show up live (local pool overweights trade-learning imitations; v02 loses to quote readers). Keep watching live |
| 3 | zoo/rival_2.py = uploads/06_rival_2.py (entries #129, #368) | below hunt_v01 live (-0.73 +-0.82) | EXCL -0.50 +-0.16 | vs hunt_v01 -4.36 | OK | Fallback only |

## Live A/B log, hunt_v02 (#393)

| Time | #393 - #383 (hunt_v01) | #393 - #368 (rival_2) | #383 - #368 | Notes |
|---|---|---|---|---|
| 02:16 | -0.39 +-0.78 (n=39) | +0.85 +-1.45 (n=27) | +0.73 +-0.82 (n=30) | #393 43 fights, mean +2.68; #383 44 fights +2.64. v02 gains vs v01: KRYPTEX +5.2, Trade Transmitters +4.6, TeenPatti +2.8, HAN SOLO +2.7, Imposters +2.4, PaperHands +1.5, Cyberpsycho +1.3, Genz7 +0.4, Quants Treasure +0.3. v02 losses: IITBHUAVENGERS -4.2, OptiMystics -4.0, AnalysisParalysis -3.8, ASYMMETRIC EDGE -3.8, MNC -3.7, Bulls Squad -3.6, Pravichayah -3.2, ThunderX -3.0, Outliers -2.6, Pokemons -1.7. House: no shared house fight yet (#393 vs sharp +16.99; #368 vs reader +22.32) |

## Local measurement log

| Time | What | Result |
|---|---|---|
| 02:18 | hunt_v02 vs hunt_v01, pool, seeds 9 10 | POOL +0.86 +-0.17. Gains vs every arena imitation (imposters +3.2, paperhands +2.6, pokemons +2.0, teenpatti +1.7, sattebaaz +1.6, outliers +0.8, QT -0.1) and rival_1 +3.1; losses vs reader -1.4, sharp -1.8, rival_2 -0.9, naive -0.3 |
| 02:19 | rival_2 vs hunt_v01, same deals | POOL -1.06 +-0.16, EXCL -0.50 +-0.16 (reader +2.0, sharp +1.6, QT +1.1; imposters -3.4) |
| 02:20 | validate + speed (tools/speed.py) | hunt_v01 OK 0.40 ms max; hunt_v02 OK 0.39 ms max |

| 02:22 | same three bots, seeds 11 12 | v02 - v01 POOL +0.83 +-0.17, EXCL +0.70 +-0.18; rival_2 - v01 EXCL -0.29 +-0.16. Confirms 9 10 |
| 02:23 | same three bots vs the 7 UNcalibrated imitations (genz7, aj, kryptex, quantumlesssss, team_how, teenpatti v1, paperhands v1), seeds 9 10 | v02 - v01 +0.80 +-0.24 (kryptex -1.5, teenpatti v1 -0.8, rest +1.2 to +2.2); rival_2 - v01 -0.88 +-0.24 |
| 02:24 | deal noise check: v02 - v01 pool average on ONE 400-deal set (seeds 9/10/11/12 separately) | +0.98 / +0.66 / +0.64 / +0.77, each +-0.25 (2se). So on a fixed field, a 400-deal average over many opponents is good to about +-0.25 |

How to read the live +-2se: tools/live_ab.py's +-2se treats the opponents as a random sample. The final is played
against (mostly) the SAME field on a new 400-deal-ish set, so the relevant noise is closer to the deal noise
(about +-0.25 for an average over many opponents). On that reading hunt_v02 - hunt_v01 = -0.39 live is about
3 standard errors below 0: hunt_v02 is likely slightly WORSE than hunt_v01 against the real field, even though
it is +0.7 to +0.9 better locally on every pool I have.

Where the live loss comes from (02:16 snapshot, split by whether the team has a zoo/arena_* imitation):

| Live paired diff | Imitated teams | NOT imitated teams (70% of the field) |
|---|---|---|
| #393 hunt_v02 - #383 hunt_v01 | +0.99 +-1.31 (n=11) | -0.93 +-0.88 (n=28) |
| #393 hunt_v02 - #368 rival_2 | +1.95 +-2.00 (n=10) | +0.21 +-1.96 (n=17) |
| #383 hunt_v01 - #368 rival_2 | +1.26 +-1.26 (n=11) | +0.42 +-1.07 (n=19) |

The imitations predict their own teams fairly well (v02 - v01: local +1.34 avg on those 11 teams, live +0.99),
but most of the field has no imitation, and against that 70% hunt_v02 loses about as much as it loses locally
to the house readers (-1.17 avg vs naive/reader/sharp). A candidate that gains only on the imitations should
be read with that in mind; its change vs reader/sharp is a rough proxy for the unimitated majority.

Local vs live agreement for v02 - v01, per imitated team: Imposters +3.2 local / +2.4 live, TeenPatti +1.7 / +2.8,
PaperHands +2.6 / +1.5, Quants Treasure -0.1 / +0.3, Sattebaaz +1.6 / +0.6 agree; Pokemons +2.0 / -1.7 and
Outliers +0.8 / -2.6 do not. Most live losses come from teams with no imitation in the pool.

---

## Update 07:40 (referee 2 takes over)

### !! #448 is NOT hunt_v10: it plays exactly like hunt_v02 (#393)
Live fight list 07:36: new entry #448 (57 fights since 07:19, mean +3.60). On the 56 opponent uploads it shares
with #393, its score is IDENTICAL to #393's on 52 and within 0.02 on the other 4 (AJ, Genz7, Balls of Wall Street,
QuantXAlpha, which use their own randomness). So the file behind #448 is hunt_v02 (or behaves exactly like it),
not hunt_v10 (hunt_v10 vs hunt_v02 head to head is -1.64 locally, they are not alike). If the owner meant to
upload hunt_v10, the wrong file went up. The live entry right now is therefore the hunt_v02 behaviour, which is
the one the live A/B says is slightly worse than hunt_v01.

Two facts this shows about the arena: (1) every live fight uses the SAME hidden deal set (a deterministic bot gets
the same score against an unchanged opponent upload), so a live paired diff per opponent has almost no deal noise:
the spread across opponents in live_ab's +-2se is real opponent-to-opponent variation; (2) only our NEWEST entry
gets new fights, so #383 (hunt_v01) stays frozen at its 44 fights; a re-upload of hunt_v01 would score exactly
what #383 scored against every opponent upload that has not changed since.

### Queue (07:40)

| Rank | File | Live paired | Local, 25-opponent pool, fresh seeds 9 10, 400 deals (diff, +-2se) | Validate / speed / header | Recommendation |
|---|---|---|---|---|---|
| 1 | versions/hunt_v10.py | not live yet (#448 is NOT it) | vs hunt_v01: ALL +0.18 +-0.05; reader-family (12) +0.00 +-0.04; imitations (11) +0.45 +-0.09; rivals -0.17. 11 extra zoo bots (team_how, teenpatti v1, paperhands v1, mid_exact, mid_steer, nova, old_plan, champ_v1, rival_3, bridge_9, attack_06): +0.53 +-0.08, no opponent below -0.10. Main session: +0.16 on seeds 11 12 | OK / 4.8 ms max under load (speed.py) / OK | Upload it NOW to get live paired evidence (vs #383 and vs #448). Locally it never costs vs the reader family, which is what hurt hunt_v02 live |
| 2 | versions/hunt_v01.py (#383) | best live record: vs rival_2 #368 +0.73 +-0.82 (n=30); vs hunt_v02 +0.38 (n=40) | base | OK / 0.40 ms / OK | Fallback / default final if hunt_v10 does not hold up live |
| 3 | versions/hunt_v02.py (#393 = #448) | vs #383 -0.38 +-0.76 (n=40; fixed-field reading about -0.38 +-0.25); not imitated teams -0.89 +-0.82 (n=30) | vs hunt_v01: ALL +0.04 +-0.10; reader-family -1.33 +-0.12; imitations +1.33 +-0.15 | OK | Do NOT leave as final |
| 4 | zoo/rival_2.py (#368) | below hunt_v01 live (-0.73 +-0.82, n=30) | vs hunt_v01: EXCL rivals +0.02; reader-family +1.02; imitations -1.07 | OK | Fallback only |

One line: the live entry (#448) is the hunt_v02 behaviour; upload versions/hunt_v10.py next for a live check, and if it
does not come out at least even with hunt_v01 on the shared opponents, re-upload versions/hunt_v01.py as the final.

### Live A/B log (referee 2). Fixed-field reading: +-0.25 (deal noise on one deal set, many opponents)

| Time | Comparison | Paired mean, +-2se (opponents as sample) | Imitated / not imitated | Notes |
|---|---|---|---|---|
| 07:36 | #393 hunt_v02 - #383 hunt_v01 | -0.38 +-0.76 (n=40) | +1.13 (n=10) / -0.89 (n=30) | frozen: #383 gets no new fights |
| 07:36 | #448 (= hunt_v02) - #383 | -0.34 +-0.86 (n=33) | +1.08 / -0.87 | same numbers as #393, fewer shared |
| 07:36 | #448 - #393 | 0.00 (n=56) | | identical bots |
| 07:36 | #383 hunt_v01 - #368 rival_2 | +0.73 +-0.82 (n=30) | +0.82 / +0.68 | frozen |
| 07:36 | #448 - #368 | +0.54 +-1.70 (n=23) | +1.53 / +0.01 | house reader: #448 +17.82 vs #368 +22.32 |

### Local calibration on the 25-opponent pool, seeds 9 10 (diff vs hunt_v01; reader-family = first 12 opponents)

| Bot | ALL 25 | reader-family 12 | imitations 11 | rivals 2 | live vs #383 |
|---|---|---|---|---|---|
| hunt_v02 | +0.04 +-0.10 | -1.33 +-0.12 | +1.33 +-0.15 | +1.08 | -0.38 (n=40) |
| rival_2 | -0.29 +-0.09 (EXCL rivals +0.02) | +1.02 +-0.11 | -1.07 +-0.16 | -3.85 (incl. mirror 0) | about -0.73 (n=30) |
| hunt_v10 | +0.18 +-0.05 | +0.00 +-0.04 | +0.45 +-0.09 | -0.17 | ? |

Both hunt_v02 and rival_2 move AWAY from hunt_v01 in opposite directions (reader-family vs imitations) and both lose
live, so hunt_v01 sits near the live optimum along that axis; no reader/imitation weighting reproduces both. hunt_v10
moves along a different axis: no change vs the reader family, gains vs imitations. If the unimitated 70% of the field
behaves like the reader family (as it did for hunt_v02), hunt_v10's expected live gain is about +0.1 to +0.15
(0.3 x 0.45): small, real if the imitations transfer, and too small for live_ab to confirm with confidence.
Head to head (seeds 9 10): hunt_v10 vs hunt_v01 -0.24 +-0.31, hunt_v10 vs hunt_v02 -1.64 +-0.57 (our own bots are not in the field).

---

## Update 07:53

### New entry #452 (first fight 07:40, 58 fights by 07:52, mean +4.62)
#452 plays like a SMALL change of hunt_v01 (per-opponent diffs vs #383 mostly within +-0.7), not like hunt_v02.
Presumably hunt_v10 (the planned upload). hunt_v11 appeared at 07:37, so the owner should confirm which file #452 is;
live data cannot tell v10 from v11 apart (they differ by about 0.1 locally).

| Time | Comparison | Paired mean, +-2se (opponents as sample) | Imitated / not imitated | Notes |
|---|---|---|---|---|
| 07:52 | #452 - #383 hunt_v01 | +0.22 +-0.23 (n=33) | +0.47 +-0.55 (n=9) / +0.13 +-0.23 (n=24) | local prediction for v10 was +0.1 to +0.3. Biggest: Quants Treasure +2.15, AnalysisParalysis +1.89, Outliers +1.38; worst MNC -1.25 |
| 07:52 | #452 - #448 (= hunt_v02) | +0.90 +-0.61 (n=55) | -0.69 / +1.25 (n=45) | house: naive +0.74, sharp +1.63, reader +2.21 |
| 07:52 | #452 - #368 rival_2 | +0.77 +-0.98 (n=23) | +1.48 / +0.39 | |

Per imitated team, live #452 - #383 vs local hunt_v10 - hunt_v01 (seeds 9 10): Outliers +1.38 / +2.28, Quants Treasure
+2.15 / +0.62, TeenPatti +0.65 / +0.30, KRYPTEX +0.06 / +0.12, Pokemons -0.14 / -0.11, Imposters -0.15 / +0.02,
Genz7 +0.02 / -0.17, Sattebaaz -0.35 / +0.03, Quantumlesssss +0.59 / -0.28, AJ -0.08 / +1.34. Signs agree on the big ones.

### hunt_v11 verification (fresh seeds, 25-opponent pool, 400 deals, diff vs hunt_v10)

| Check | Result |
|---|---|
| seeds 9 10 | ALL +0.083 +-0.037; reader-family (12) +0.053 +-0.038; imitations (11) +0.142 +-0.069; rivals -0.06 |
| seeds 11 12 | ALL +0.107 +-0.037; reader-family +0.066 +-0.038; imitations +0.152 +-0.070; rivals +0.11 |
| 11 extra zoo bots, seeds 9 10 | +0.088 +-0.065 (teenpatti v1 +0.84, nova +0.50; mid_steer -0.22) |
| per opponent (both seed pairs) | gains hider +0.74/+0.92, outliers +0.47/+0.44, mid_guard +0.31/+0.33, pokemons +0.32/+0.26; costs quants_treasure -0.40/-0.43, ai_typical -0.13/-0.27 |
| head to head (seeds 9 10) | vs hunt_v10 +0.52 +-0.28, vs hunt_v01 +0.24 +-0.28, vs hunt_v02 -1.63 +-0.57 |
| validate / speed / header | OK / median 0.28 ms, max 9.7 ms under heavy machine load (speed.py) / OK |

Verdict: hunt_v11 is a small but consistent improvement over hunt_v10 on every pool and seed pair (+0.08 to +0.11,
about 2.5 se each), with no group losing. It has no live record yet.

### Queue (07:53)

| Rank | File | Live paired | Local fresh seeds (25-opponent pool) | Recommendation |
|---|---|---|---|---|
| 1 | versions/hunt_v11.py | none yet | vs hunt_v10 +0.08 (9 10), +0.11 (11 12); so vs hunt_v01 about +0.27 | Candidate for the next upload once #452 has its first ~50 fights (it already has 58), so its live record is settled |
| 2 | versions/hunt_v10.py (= #452, to be confirmed) | vs #383 +0.22 +-0.23 (n=33); vs #448/hunt_v02 +0.90 +-0.61 (n=55) | vs hunt_v01 +0.18 (9 10), +0.16 (11 12, main session) | Current live best |
| 3 | versions/hunt_v01.py (#383) | vs #368 +0.73 (n=30) | base | Fallback |
| 4 | versions/hunt_v02.py (#393, #448) | vs #383 -0.38 (n=40) | | Do not use |
| 5 | zoo/rival_2.py (#368) | vs #383 -0.73 (n=30) | | Do not use |

One line: #452 (hunt_v10 presumably) is the best live entry so far and is live now; uploading hunt_v11 next is a small,
locally consistent step (+0.1) that live data will barely be able to confirm; if hunt_v11 shows below #452 on the shared
opponents by more than about 0.3, go back to hunt_v10.

---

## Update 08:10

### !! New entry #456 (first fight 08:01) is NOT a hunt_v1N file and is worse than #452
#456 plays like the attack/merge line: house reader +30.00 and sharp +25.63 (vs #452: +20.03 / +18.63), heavy losses to the
trade-learning teams (Sattebaaz -6.90, Imposters -6.17, AJ -3.67, TeenPatti -3.10, KRYPTEX -2.78, Pokemons -2.68 vs #452).
On the 9 opponent uploads it shares with #328 (attack_v05) it is within -0.05 +-0.32 of it. hunt_v13's crush only adds about
+3.6 vs reader, so #456 is not hunt_v13 either. If this was meant to be hunt_v13 (or v12), the wrong file went up again.

| Time | Comparison | Paired mean, +-2se (opponents as sample) | Imitated / not imitated | Notes |
|---|---|---|---|---|
| 08:08 | #456 - #452 | -0.61 +-0.73 (n=57) | -2.57 +-1.46 (n=10) / -0.20 +-0.78 (n=47) | fixed-field reading: clearly worse (a big behaviour change, so its deal noise is about +-0.25: -0.61 is about 5 se) |
| 08:08 | #456 - #383 | -0.94 +-0.91 (n=32) | -2.35 / -0.39 | |
| 08:08 | #452 - #383 | +0.22 +-0.23 (n=33) | +0.47 / +0.13 | unchanged (frozen since #456 went up) |

So the live entry right now (#456) is a step BACK. Re-upload a hunt_v1N file.

### Deal noise of the v10 - v01 difference on one 400-deal set (fixed-field reading)
hunt_v10 - hunt_v01 on the 25-opponent pool, one 400-deal set each: seed 9 +0.21, 10 +0.17, 11 +0.18, 12 +0.13 (each +-0.065
by eval.py; spread sd 0.03). The previous referee's +-0.25 was for hunt_v02 - hunt_v01, a much bigger behaviour change. For
small changes like v10/v11/v12 vs v01 the fixed-field noise of a many-opponent average is about +-0.06 to +-0.1, so #452 - #383
= +0.22 on 33 opponents is clearly positive on the fixed-field reading (+0.22 +-0.23 on the opponents-as-sample reading).

### hunt_v12 and hunt_v13 verification (fresh seeds, 25-opponent pool, 400 deals, diff vs hunt_v10)

| File | seeds 9 10: ALL / reader-family (12) / imitations (11) / rivals | seeds 11 12 | 11 extra zoo bots (9 10) | validate / speed (quiet) / header |
|---|---|---|---|---|
| hunt_v11 | +0.083 +-0.037 / +0.053 / +0.142 / -0.06 | +0.107 +-0.037 | +0.088 +-0.065 | OK / under 1 ms / OK |
| hunt_v12 | +0.245 +-0.044 / +0.015 +-0.043 / +0.478 +-0.081 / +0.35 | (not run; 5.5 se on 9 10) | +0.11 (teenpatti v1 +0.59, nova +0.72; mid_steer -0.63) | OK / 0.35 ms max / OK |
| hunt_v13 | +0.411 +-0.048 / +0.366 +-0.059 / +0.471 +-0.081 / +0.35 | +0.357 +-0.047 / +0.319 / +0.431 / +0.18 | v13 - v12: +0.22 (crush fires only on mid_exact +1.11, champ_v1 +1.09; every other bot 0.00 to +0.17) | OK / 0.83 ms max in 2 quiet runs (one 10 ms and one 56 ms spike only while the machine was at load 9-11) / OK |

hunt_v13 - hunt_v12 = the crush of exact house-formula readers: reader +3.6/+3.0, sharp +1.0/+0.8, swapper +0.3, mid_exact +1.1,
champ_v1 +1.1; costs sharp_t05 -0.6/-0.5 and ai_typical -0.2 (both seed pairs); zero on every arena imitation. In the live
field it should fire on the house reader and sharp (about +4.5 / 57 fights = +0.08 on the average) and on any team that
quotes the reader formula exactly (gain if it also responds like reader/sharp, loss like sharp_t05 if it trades more eagerly).
Main risk: a team that copied the reader quote formula but trades on a lower threshold. Live A/B will show it as a big
negative diff against a non-imitated team.

### Queue (08:10)

| Rank | File | Live paired | Local fresh seeds (vs hunt_v10, 25-opponent pool) | Recommendation |
|---|---|---|---|---|
| 1 | versions/hunt_v13.py | none yet | +0.41 (9 10), +0.36 (11 12); reader-family +0.37/+0.32; imitations +0.47/+0.43 | UPLOAD NOW (replaces #456). Then check vs #452 on the shared opponents |
| 2 | versions/hunt_v12.py | none | +0.25 (9 10); reader-family +0.02, imitations +0.48 | Fallback if hunt_v13's crush misfires live (big loss to a team) |
| 3 | versions/hunt_v11.py | none | +0.08 / +0.11 | superseded by v12 |
| 4 | versions/hunt_v10.py (#452, presumably) | vs #383 +0.22 +-0.23 (n=33); vs #448 +0.90 (n=55); vs #456 +0.61 (n=57) | base | Best LIVE record; the safe final if nothing newer holds up |
| 5 | versions/hunt_v01.py (#383) | vs #368 +0.73 (n=30) | -0.18 | |
| 6 | #456 (attack/merge-line file), hunt_v02 (#393/#448), rival_2 (#368) | all below #452 live | | Do not leave any of these as the final |

One line: the live entry #456 is worse than #452; upload versions/hunt_v13.py now; final = hunt_v13 if its live diff vs #452
is >= about 0 with no single team losing big from the crush, else hunt_v12 or re-upload hunt_v10.
