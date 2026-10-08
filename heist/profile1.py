"""heist/profile1.py - first-quote profile of every opponent in our fights (deal 1).

For each fight of entry E (default 452), the opponent's:
  q0   r1 quote as the FIRST quoter (seat 0, hand 32; naive fair 102.62)
  r0   its r1 response to our r1 quote when we quote first (we hold 32 in seat 0)
  q1   its r1 quote as the SECOND quoter (seat 1, hand 40; naive fair 108.94), and q1 - our r1 quote
  swaps / peeks rounds
"""
import json
import os
import sys

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fights")
E = int(sys.argv[1]) if len(sys.argv) > 1 else 452
team = "Alpha Rodeo"
rows = []
for fn in sorted(os.listdir(DATA)):
    d = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
    if E not in (d["a_id"], d["b_id"]):
        continue
    me = team if team in (d["a"], d["b"]) else (d["a"] if d["a_id"] == E else d["b"])
    opp = d["b"] if d["a"] == me else d["a"]
    my_score = d["score_a"] if d["a"] == me else d["score_b"]
    info = {"opp": opp, "score": my_score}
    for p in d["plays"]:
        s = p["seats"]
        o = s.index(opp)
        r1 = p["rounds"][0]
        qs = r1["quotes"]
        mv = []
        for r in p["rounds"]:
            m = r["moves"][o]
            if m:
                mv.append(f"{m['kind'][0]}{r['round']}")
        if o == 0:
            info["q0"] = qs[0]["price"]
            info["resp_to_our_r1"] = qs[1]["qty"]
            info["mv0"] = "".join(mv)
        else:
            info["our_q"] = qs[0]["price"]
            info["q1"] = qs[1]["price"]
            info["r1resp"] = qs[0]["qty"]
            info["mv1"] = "".join(mv)
    rows.append(info)
rows.sort(key=lambda x: x["score"])
print(f"{'opponent':<22}{'our score':>9} {'q0':>8} {'q1':>8} {'our_q':>8} {'q1-ourq':>8} {'resp':>5} moves")
for x in rows:
    print(f"{x['opp']:<22}{x['score']:+9.2f} {x.get('q0', 0):8.2f} {x.get('q1', 0):8.2f} {x.get('our_q', 0):8.2f} "
          f"{x.get('q1', 0) - x.get('our_q', 0):+8.2f} {x.get('r1resp', 0):+5d} {x.get('mv0', '')}/{x.get('mv1', '')}")
