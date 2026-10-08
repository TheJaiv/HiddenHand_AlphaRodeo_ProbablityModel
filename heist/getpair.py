"""heist/getpair.py - fetch the fight between two entries (or an entry and a team's newest entry).

    python3 -I heist/getpair.py 452 376 466 463 ...      pairs of entry ids: fetch each fight
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replays import DATA, fight   # noqa: E402

fl = json.load(open(os.path.join(DATA, "fights.json"), encoding="utf-8"))
idx = {}
for f in fl:
    idx[(f["a_id"], f["b_id"])] = f
    idx[(f["b_id"], f["a_id"])] = f
args = [int(x) for x in sys.argv[1:]]
for x, y in zip(args[::2], args[1::2]):
    f = idx.get((x, y))
    if not f:
        print(f"#{x} vs #{y}: no fight")
        continue
    d = fight(f["href"])
    print(f"#{x} vs #{y}: {d['a']} {d['score_a']:+.2f} / {d['b']} {d['score_b']:+.2f}")
