You are building the final competition bot for team "Alpha Rodeo" in Hidden Hand, a bot tournament run by The Quant Club, IIT BHU. Uploads close TONIGHT, Thursday 8 October 2026, end of day. Only the final run counts: our newest upload plays every other team's newest upload on fresh deals. Your only goal is the highest score against the REAL field of teams on the live arena. Do not optimise for local test pools.

## Where you work
Repo /Users/jaiv/Coding/hiddenhand/tqc-hiddenhand-moneyheist, git branch `heist` (already checked out). Work only in the `heist/` folder and commit there.
- Read README.md, rules.py and engine.py first: the game and the scoring.
- `heist/tokyo.py` is the reference to beat (live entry #452, our best paired live record so far).
- Bots are named after Money Heist characters, in the order listed in `heist/LEDGER.md` (berlin, nairobi, rio, denver, ...). Each accepted bot takes the next unused name. `heist/professor.py` is a copy of the bot chosen as the FINAL upload.
- Ignore every older bot and test pool in versions/ and zoo/. Do not tune against zoo/ bots, the house bots alone, or rival_* bots.
- Usable tools:
  - `tools/live_ab.py`: reads the public fight list and compares our live uploads on the same opponents.
  - `tools/speed.py`: per-call timing.
  - `tools/eval.py`: local matches, only with the field imitations described below.
  - `zoo/arena_raw/`: older public replays. Its README.md documents the and uJSON format; refresh the data.

## Hard rules (breaking them can disqualify the team)
- `exploiter.py` in the repo root is another team's code. NEVER open, read, import, run or copy it, and never use another team's code or numbers. Learn about other teams ONLY from the public arena pages: standings, fight lists, replays.
- Fetch public pages only, politely: plain GETs, at most about 1 request per second, cache what you fetch under `heist/data/`. No logins, no other endpoints.
- Bot file rules:
  - The first three lines must be exactly:
    # Team Name: Alpha Rodeo
    # Members: Jaiv Patel(26075057)
    # Mentor: Arpit Gupta
  - Standard library imports only: math, random, statistics, collections, heapq, bisect, itertools, functools, typing.
  - No network or file access inside the bot. Nothing kept between deals.
  - Must pass `python backtester.py --validate`. Slowest call under 10 ms (`python tools/speed.py`).
- Never edit engine.py, rules.py, backtester.py, bot_loader.py or strategies/.

## The method: the field is the test
1. **Census.** Use Python scripts to download the standings and the full public fight list from https://hiddenhand.tqciitbhu.org (the site root has the standings; /fights has the fight list; individual fight pages have replays). For every team's NEWEST entry, build the score matrix: who beats whom, and by how much. Save it as `heist/data/matrix.json` and summarise it in `heist/FIELD.md`:
   - the top 15 teams;
   - which teams beat our entries and which we beat;
   - which teams beat the top teams.
2. **Profile every team that matters**: the top 15, every team that beats us, and every team whose result against us varies a lot between our entries. Use replays: their first quote, how their quotes move with their hand and with our quotes and trades, how they answer quotes (threshold, lot size), swap and peek habits. Group teams into a few styles and record each team's style and evidence in FIELD.md.
3. **Field model.** Write an imitation for each important style (`heist/opp_<team>.py`). Calibrate every imitation against the live matrix: our live entries' scores against that team must be matched locally within about 1.5 (run the same bot files locally against the imitation). Drop or fix imitations that do not calibrate. Weight the field model by how many live teams share each style. The house bots naive, reader and sharp are part of the real field, so include them at their real share (3 of about 57 teams).
4. **Improve**, starting from tokyo.py, or from a fresh design if the profiles show a clearly better approach. Make one change at a time. Keep a change only if:
   - it gains on the calibrated field model by more than 2 standard errors on two different seed pairs; and
   - it does not fall below tokyo against any of the top 10 teams' imitations by more than 1.
5. **Verify live.** The live arena is the final judge. The owner uploads one file every 10 minutes. After about 40 fights, compare it with the previous upload using `tools/live_ab.py` (same opponent uploads, paired). A version that is worse live is dropped, whatever the local numbers say.
6. **Save** every accepted bot as a new file `heist/<next name>.py`, with the 4th line "# Version: <name> (vNN), parent <name>, idea: ...". Never edit a saved file. Log every version and every rejected idea, with numbers, in `heist/LEDGER.md`, and commit. When a final is chosen, copy it to `heist/professor.py`.

## What to report, and how often
Report every 60 to 90 minutes, short and plain:
- **UPLOAD NOW**: one file name, and why.
- **FALLBACK**: the best file with a proven live record.
- Our current live rank and score, and the live paired results of our last uploads.
- What the field census says: the top styles, who beats us and why.

Time plan: the census and profiles within 60 minutes, a first improved upload within 2 hours, then keep iterating. Three hours before the deadline, stop changing behaviour. From then on, only choose between files that already have live records.
