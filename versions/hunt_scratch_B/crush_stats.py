"""crush_stats.py BOT OPP [deals] - how often / when BOT quotes an extreme price (0 or >=190) vs OPP."""
import sys, random, statistics as st
from pathlib import Path
KIT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(KIT))
from backtester import resolve
from bot_loader import load_for_testing
from engine import play_deal, derive_seed
bot, opp = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 100
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 5
B = load_for_testing(str(resolve(bot).resolve()), quiet=True)
O = load_for_testing(str(resolve(opp).resolve()), quiet=True)
first_round = []
pairs = []
crush_pairs = []
for d in range(n):
    s = derive_seed(seed, d)
    tot = 0
    crushed = False
    for k, sw in enumerate((False, True)):
        random.seed(derive_seed(seed, "rng", 2 * d + k))
        b, o = B(), O()
        res = play_deal(o, b, s) if sw else play_deal(b, o, s)
        me = 1 if sw else 0
        tot += res["pnl"][me]
        for row in res["log"]["rounds"]:
            for q in row["quotes"]:
                if q["maker"] == me and (q["price"] <= 0.5 or q["price"] >= 190):
                    first_round.append(row["round"]); crushed = True
                    break
            else:
                continue
            break
    pairs.append(tot)
    if crushed:
        crush_pairs.append(tot)
sq = lambda p: (abs(p) ** .5) * (1 if p >= 0 else -1)
print(f"{Path(bot).stem} vs {Path(opp).stem}: {n} deal pairs, score {st.mean(map(sq, pairs)):+.2f}; "
      f"plays with an extreme quote: {len(first_round)} (rounds {sorted(first_round)[:40]}); "
      f"score of pairs with a crush {st.mean(map(sq, crush_pairs)) if crush_pairs else float('nan'):+.2f} n={len(crush_pairs)}")
