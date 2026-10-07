# Upload track

The files to upload to the arena, in order. Each entry is strictly better than the one above it:
measured against the SAME full pool on fresh seeds the agents never tuned on, it must
1. beat the previous entry's WEIGHTED score by more than the error bar,
2. not lose head to head to the previous entry,
3. not drop more than 0.5 against rival_1, rival_2 or rival_3,
4. pass --validate and stay under 10 ms per call.
Only Claude adds entries, after its own check. Upload the newest entry; if the live board looks
worse after it, go back one entry.

| # | File | Weighted (check seeds) | vs previous | vs r1 / r2 / r3 | What changed | Added |
|---|---|---|---|---|---|---|
| 1 | versions/bridge_v01.py | +8.51 (seeds 1 2) | - | +2.7 / -2.4 / +3.1 | starting point (bridge_11_strong) | Wed |
| 2 | versions/duel_v04.py | +8.81 (seeds 7 8; prev +7.99) | +0.96 head to head | +4.2 / +0.9 / +4.2 | reads swappers better, hides 40% of its hand from round 2 vs unknown bots, stronger skew, late taker margin, ignores probe quotes | Wed |
| 3 | versions/merge_v05.py | +9.23 (seeds 9 10; prev +8.42) | tie (-0.03) head to head | +4.1 / +0.8 / +4.0 | duel_v04 + farm_v04 merged: recognises ai_typical-style bots exactly (+12 vs ai_typical) and reads hiders from their trades (+1.1 vs hider) | Wed |
| 4 | versions/merge_v07.py | +9.50 (seeds 15 16; merge_v05 +7.29 same run) | +1.42 head to head (seeds 17 18) | +4.7 / +3.4 / +4.5 | merge_v05 + attack_v06: paid 195/0 vs readers, falling swap bar, hidden first quote; skew 0.4. vs rival_2 +3.8 (seeds 17 18) | Thu |
