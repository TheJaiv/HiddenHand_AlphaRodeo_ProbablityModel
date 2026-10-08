"""crush_list.py BOT OPP [deals] [seed] - list plays where BOT quotes 0 / >=190, with its position before the quote."""
import sys, random
from pathlib import Path
KIT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(KIT))
from bot_loader import load_for_testing
from backtester import resolve
from engine import play_deal, derive_seed
B = load_for_testing(str(resolve(sys.argv[1]).resolve()), quiet=True)
O = load_for_testing(str(resolve(sys.argv[2]).resolve()), quiet=True)
n = int(sys.argv[3]) if len(sys.argv) > 3 else 40
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 5
for d in range(n):
    s = derive_seed(seed, d)
    for k, sw in enumerate((False, True)):
        random.seed(derive_seed(seed, "rng", 2 * d + k))
        b, o = B(), O()
        res = play_deal(o, b, s) if sw else play_deal(b, o, s)
        me = 1 if sw else 0
        pos = 0
        for row in res["log"]["rounds"]:
            for q in row["quotes"]:
                if q["maker"] == me:
                    if q["price"] <= 0.5 or q["price"] >= 190:
                        print(f"deal {d} swap {sw} round {row['round']} pos {pos:+d} price {q['price']} qty {q['qty']} pnl {res['pnl'][me]:+.1f}")
                    pos -= q["qty"]
                else:
                    pos += q["qty"]
