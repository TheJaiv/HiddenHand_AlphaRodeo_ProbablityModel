"""For each team quote made against a house bot, the house bot's fair when answering it."""
import sys, importlib.util
import tapes
R = "/Users/jaiv/Coding/hiddenhand/tqc-hiddenhand-moneyheist/strategies/"
def load(n):
    spec = importlib.util.spec_from_file_location(n, R + n + ".py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m.Bot
H = {"House · naive": load("naive"), "House · reader": load("reader"), "House · sharp": load("sharp")}
team_dir, team, entry = sys.argv[1], sys.argv[2], int(sys.argv[3])
for base, d in tapes.load(team_dir, entry, team):
    for p in d["plays"]:
        if team not in p["seats"]: continue
        opp = [s for s in p["seats"] if s != team][0]
        if opp not in H: continue
        me = p["seats"].index(team); hs = 1 - me
        # house bot's own decisions in this play, in order
        bot = H[opp]()
        mine = list(tapes.decisions(p, me))
        theirs = list(tapes.decisions(p, hs))
        print(f"== {opp} seat{me} hand {mine[0][1].hand}")
        mq = [x for x in mine if x[0] in ("quote", "respond")]
        th = [x for x in theirs if x[0] in ("quote", "respond")]
        for (k1, o1, a1, e1), (k2, o2, a2, e2) in zip(mq, th):
            if k1 == "quote":
                f = bot.fair(o2) if hasattr(bot, "fair") else None
                print(f"  r{e1['round']} pos{o1.position:+3d} {team[:6]} quotes {a1:7.2f}  house fair {f:7.2f}  house-quote={f - a1:+6.2f}  -> house did {a2:+d}")
            else:
                f = bot.fair(o2) if hasattr(bot, "fair") else None
                print(f"  r{e1['round']} pos{o1.position:+3d} house quotes {e1['price']:7.2f} (its fair {f:7.2f}); {team[:6]} did {a1:+d}")
