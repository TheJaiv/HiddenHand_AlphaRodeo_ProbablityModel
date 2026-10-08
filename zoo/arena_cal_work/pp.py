import json, sys
def pp(fn):
    d = json.load(open(fn))
    print(f"### {d['a']} {d['score_a']:+.2f} vs {d['b']} {d['score_b']:+.2f}")
    for p in d["plays"]:
        s = p["seats"]
        print(f"  seat0 {s[0]} {p['hand_ranks'][0]} sum {sum(p['hand_ranks'][0])} | seat1 {s[1]} {p['hand_ranks'][1]} sum {sum(p['hand_ranks'][1])} | V {p['V']}")
        for r in p["rounds"]:
            mv = " ".join(f"{s[i][:6]}:{m['kind']}{(' '+m.get('out','')+'->'+m.get('in','')) if m['kind']=='swap' else ''}" for i, m in enumerate(r["moves"]) if m)
            qs = "  ".join(f"{s[q['maker']][:8]}@{q['price']:.2f}->{q['qty']:+d}" for q in r["quotes"])
            print(f"    r{r['round']} {mv:30s} {qs}")
        print(f"    pos {p['positions']} pnl {p['pnl']}")
for fn in sys.argv[1:]:
    pp(fn)
