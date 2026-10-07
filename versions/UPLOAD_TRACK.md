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
