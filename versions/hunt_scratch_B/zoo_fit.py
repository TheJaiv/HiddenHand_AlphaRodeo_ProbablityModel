"""zoo_fit.py - same regression as field_fit.py, on local games of zoo bots vs some opponents."""
import sys, random
from pathlib import Path
KIT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(KIT)); sys.path.insert(0, str(KIT / "tools"))
from backtester import resolve
from bot_loader import load_for_testing
from engine import play_deal, derive_seed, rank
sys.argv += []
exec(open(Path(__file__).parent / "field_fit.py").read().split("def ols")[0].split("fl = json.load")[0])
src = open(Path(__file__).parent / "field_fit.py").read()
ols_src = "def ols" + src.split("def ols")[1].split("print(f\"{'team'")[0]
exec(ols_src)
OPPS = ["versions/hunt_v10.py", "naive", "zoo/rival_2.py", "zoo/arena_imposters.py"]
def rows_for(bot):
    B = load_for_testing(str(resolve(bot).resolve()), quiet=True)
    rows = []
    for o in OPPS:
        O = load_for_testing(str(resolve(o).resolve()), quiet=True)
        for d in range(25):
            s = derive_seed(99, d)
            random.seed(s)
            res = play_deal(B(), O(), s)
            p = res["log"]
            i = 0
            hand = [rank(c) for c in p["hands"][i]]
            board = [rank(c) for c in p["board"]]
            disc = []; opp_last = None
            for row in p["rounds"]:
                r = row["round"]
                for j, mv in enumerate(row["moves"]):
                    if mv and mv.get("kind") == "swap":
                        disc.append(rank(mv["out"]))
                        if j == i:
                            hand.remove(rank(mv["out"])); hand.append(rank(mv["in"]))
                shown = board[:r - 1]
                unseen = [4] * 13
                for c in hand + shown + disc:
                    unseen[c - 1] -= 1
                U = sum(unseen); m = sum((k + 1) * c for k, c in enumerate(unseen)) / U
                nb = len(shown)
                for q in row["quotes"]:
                    if q["maker"] == i:
                        naive = sum(hand) + sum(shown) + (10 - nb) * m
                        if opp_last is not None:
                            imp = opp_last - sum(shown) - (10 - nb) * m
                            rows.append((q["price"] - naive, imp - 5 * m, sum(hand) - 5 * m, r))
                    else:
                        opp_last = q["price"]
    return rows
for b in sys.argv[1:]:
    fit = ols(rows_for(b))
    (a, b1, b2), s = fit
    print(f"{Path(b).stem:<24} a {a:+6.2f}  b1 {b1:+5.2f}  b2 {b2:+5.2f}  resid {s:5.2f}")
