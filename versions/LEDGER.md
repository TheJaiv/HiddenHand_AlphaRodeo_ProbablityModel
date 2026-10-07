# Bridge versions

Every accepted upgrade of the bridge line is a full, standalone, upload-ready file here.
Never edit a saved version: make a new one. Each agent branch keeps its own ledger
(versions/LEDGER_<line>.md) and merges are recorded here.

Acceptance rule for a new version: weighted score beats its parent by more than 2 error bars on
seeds 1 2 (tools/eval.py --deals 300), the gain is confirmed on seeds 5 6, no head to head against
rival_1 / rival_2 / rival_3 drops by more than 0.5, slowest call (tools/speed.py) under 10 ms,
and python backtester.py --validate passes.

| Version | Parent | Branch | Pool | Weighted | vs r1 | vs r2 | vs r3 | Idea |
|---|---|---|---|---|---|---|---|---|
| bridge_v01 | - | lab | +10.08 | +8.51 | +2.73 | -2.41 | +3.13 | zoo/bridge_11_strong.py as built |
