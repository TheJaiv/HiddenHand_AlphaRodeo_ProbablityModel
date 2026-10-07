You are helping team "Alpha Rodeo" in Hidden Hand, a bot competition (The Quant Club, IIT BHU). Final uploads close tonight, Thursday 8 October 2026, end of day. Goal: find a bot that beats rival_2 against the REAL live field, and ideally beats every team.

## The repo
/Users/jaiv/Coding/hiddenhand/tqc-hiddenhand-moneyheist, branch `lab`. Read README.md, rules.py and engine.py first (the game). Then:
- tools/eval.py (bot vs a pool of opponents, mirrored deals, prints the ranked score), tools/speed.py (per-call timing), tools/trace.py (one deal with a bot's internals).
- zoo/: local opponents and zoo/weights.json. zoo/rival_1.py, rival_2.py, rival_3.py are our strongest bots. zoo/arena_*.py are imitations of real arena teams.
- zoo/arena_raw/: public replays of live fights, one JSON per fight. Format and caveats are in zoo/arena_raw/README.md. Each file has the 400-deal live result (score_a / score_b) and the first deal played both ways.
- versions/: our upgraded bots (bridge, duel, farm, attack, merge lines), versions/LEDGER*.md and versions/UPLOAD_TRACK.md.
Never edit engine.py, rules.py, backtester.py, bot_loader.py or strategies/.

## What we know (facts, not guesses)
1. rival_2 is our best LIVE bot. As entry #129 it played 38 teams: mean score +5.96, 32 wins out of 38. Its worst opponents: Quants Treasure -4.0, TeenPatti -3.2, Quantumlesssss -1.1, Happy Happy -0.5, Imposters -0.3, KRYPTEX -0.1. Source: zoo/arena_raw/alpha_rodeo/129_vs_*.json.
2. versions/merge_v07.py and versions/attack_v05.py beat rival_2 LOCALLY: weighted +9.50 and +8.41 against +7.37, and merge_v07 beats it +3.8 head to head. LIVE, the owner saw both do clearly WORSE than rival_2.
3. So our local pool is mis-calibrated. Likely reasons, to verify not assume:
   - the pool is full of reader-family bots (house bots, sharp variants, mid_* and bridge_*), and our attack layer farms those;
   - the attack line's paid extreme quotes (195 / 0 short of the position limit) and the "identified reader" check may misfire on real bots that clamp or ignore odd quotes;
   - the arena_* imitations come from one deal per fight and may be inaccurate.

## Your task, in order
1. Diagnose the live gap. If the arena fight pages for our newer entries are public (earlier scraping used plain GETs of public fight pages on https://hiddenhand.tqciitbhu.org; stay polite, at most about 1 request per second), fetch the fights of our merge_v07 and attack_v05 entries. Compare them opponent by opponent with rival_2's entry #129, and find which teams and which behaviours cost us. If you cannot fetch, ask the owner for screenshots of those entries' fight lists.
2. Build a CALIBRATED pool. Write imitations of the live teams that matter most: our worst opponents above, the top of the standings, and the most common styles in arena_raw. Decode each from its replays, as the existing zoo/arena_*.py did. Check every imitation: rival_2's local score against it (tools/eval.py --vs, 500 deals) must be within about 1.5 of rival_2's live score against that team. Fix or drop imitations that fail. Weight the pool to match the live field (about 40 teams), not the zoo.
3. Prove the calibration. On the calibrated pool, the local order must reproduce the live order: rival_2 above merge_v07 and attack_v05. Until it does, do not trust any local improvement.
4. Improve, starting from zoo/rival_2.py. Make one change at a time and keep it only if it beats its parent on the calibrated pool by more than 2 standard errors on two different seed pairs, without losing to rival_2 head to head. Ideas with evidence:
   - a hider detector: ignore opponent quotes within 0.02 of the public estimate (+5.7 vs a hider, +0.38 pool on the old pool);
   - rival_2 loses mostly as the MAKER against strong bots (vs rival_1: maker -42.5 per game, taker +21.8);
   - duel line pieces: condition the opponent's kept cards on its swap discard; hide 40% of our hand in quotes from round 2 against unidentified bots (see versions/duel_v02-v04 and LEDGER_duel.md);
   - target the teams we lose to live, using their imitations.
   Do NOT carry over the paid extreme quotes, or anything else, unless it wins on the calibrated pool.
5. Save every accepted bot as a new file versions/hunt_vNN.py. Its first lines must be exactly:
   # Team Name: Alpha Rodeo
   # Members: Jaiv Patel(26075057)
   # Mentor: Arpit Gupta
   followed by "# Version: hunt_vNN, parent ..., idea: ...". Never edit a saved file. Log each version, and each rejected idea, in versions/LEDGER_hunt.md, and commit on `lab`.

## Rules the bot file must follow
- Standard library imports only: math, random, statistics, collections, heapq, bisect, itertools, functools, typing.
- No network or file access inside the bot. Nothing kept between deals.
- Must pass python backtester.py --validate.
- Slowest call under 10 ms (python tools/speed.py <file>).

## Time box
Deliver a first upload candidate within about 2 hours, even a small gain over rival_2, then keep improving. Report:
- what caused the live gap;
- the calibration check (rival_2 local vs live, for each imitation);
- a ranked list of upload candidates, each beating rival_2 on the calibrated pool, with a plain-words explanation of what each changes.
