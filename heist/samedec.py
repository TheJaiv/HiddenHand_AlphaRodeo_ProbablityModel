"""heist/samedec.py - do two bot files make the same decisions on every cached replay of an entry?

    python3 -I heist/samedec.py A.py B.py ENTRY [ENTRY ...]

For each fight of our entry, our seat is replayed with the real opponent actions (as in
match_replay.py) and A's and B's decisions are compared. Lists the fights where they differ.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from bot_loader import load_for_testing   # noqa: E402
import match_replay as M                   # noqa: E402

A = load_for_testing(sys.argv[1], quiet=True)
B = load_for_testing(sys.argv[2], quiet=True)
ents = [int(x) for x in sys.argv[3:]]
D = os.path.join(HERE, "data", "fights")
diff = 0
tot = 0
for fn in sorted(os.listdir(D)):
    d = json.load(open(os.path.join(D, fn), encoding="utf-8"))
    if d["a_id"] not in ents and d["b_id"] not in ents:
        continue
    team = d["a"] if d["a_id"] in ents else d["b"]
    opp = d["b"] if team == d["a"] else d["a"]
    tot += 1
    for p in d["plays"]:
        i = p["seats"].index(team)
        # record A's decisions as the "real" ones by replaying A, then check B against the same history
        ra = M.replay_seat(A, p, i)
        rb = M.replay_seat(B, p, i)
        if ra != rb:
            diff += 1
            print(f"  differs: {fn} vs {opp}: A {ra[0]}/{ra[1]} first miss {ra[2]} | B {rb[0]}/{rb[1]} first miss {rb[2]}")
print(f"{tot} fights checked, {diff} plays where the two files differ")
