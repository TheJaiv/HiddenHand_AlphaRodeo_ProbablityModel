"""heist/show.py - print parsed fights compactly: python3 -I heist/show.py A_B.json ..."""
import json
import sys

for fn in sys.argv[1:]:
    d = json.load(open(fn, encoding="utf-8"))
    print(f"=== {d['a']} #{d['a_id']} {d['score_a']:+.2f} vs {d['b']} #{d['b_id']} {d['score_b']:+.2f}  (pnl/deal {d['pnl_a']:+.1f})")
    for p in d["plays"]:
        s = p["seats"]
        print(f"  seat0 {s[0]} {p['hand_ranks'][0]} ({sum(p['hand_ranks'][0])}) | seat1 {s[1]} {p['hand_ranks'][1]} "
              f"({sum(p['hand_ranks'][1])}) | board {p['board_ranks']} V={p['V']}")
        for r in p["rounds"]:
            mv = []
            for i, m in enumerate(r["moves"]):
                if m:
                    mv.append(f"{s[i][:6]}:{m['kind']}" + (f" {m['out']}->{m['in']}" if m['kind'] == 'swap' else ""))
            qs = []
            for q in r["quotes"]:
                qs.append(f"{s[q['maker']][:6]} q{q['price']:.2f}->{q['qty']:+d}")
            print(f"    r{r['round']} {' '.join(mv):<34} " + "   ".join(qs))
        print(f"    pos {p['positions']} paid {p['paid']} pnl {p['pnl']}")
