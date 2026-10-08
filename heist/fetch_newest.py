"""heist/fetch_newest.py - cache up to N fights of every team's newest entry (polite: 1 GET / 1.2 s).

    python3 -I heist/fetch_newest.py [N]
Fights against our own newest entries come first, then the most recent others.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replays import DATA, OUT, fight   # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
m = json.load(open(os.path.join(DATA, "matrix.json"), encoding="utf-8"))
fl = json.load(open(os.path.join(DATA, "fights.json"), encoding="utf-8"))
have = set(os.listdir(OUT)) if os.path.isdir(OUT) else set()
ours = sorted((int(e) for e in m["ours"]), reverse=True)[:3]
n_get = 0
for team, e in sorted(m["newest"].items()):
    if team == "Alpha Rodeo" or not e:
        continue
    fs = [f for f in fl if e in (f["a_id"], f["b_id"])]
    fs.sort(key=lambda f: (0 if (f["a_id"] in ours or f["b_id"] in ours) else 1))
    cnt = 0
    for f in fs:
        if cnt >= N:
            break
        fn = f"{f['a_id']}_{f['b_id']}.json"
        if fn not in have:
            fight(f["href"])
            n_get += 1
        cnt += 1
    print(f"{team} #{e}: {cnt} fights cached", flush=True)
print("fetched", n_get)
