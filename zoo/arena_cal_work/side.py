"""Teacher-forced side by side: python side.py BOT.py DIR "Team" ENTRY [opp_filter]"""
import sys, tapes, fidelity
bot_path, d, team, entry = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
flt = sys.argv[5] if len(sys.argv) > 5 else ""
Bot = fidelity.load_bot(bot_path)
cur = None
for kind, o, act, ex in tapes.team_decisions(d, team, entry):
    if flt not in ex["fight"]:
        continue
    key = (ex["fight"], ex["seat"])
    if key != cur:
        cur, bot = key, Bot()
        print(f"\n== {ex['fight']} seat{ex['seat']} hand {o.hand}")
    if kind == "move":
        g = bot.move(o)
        if g or act:
            print(f"  r{ex['round']} move real={act} bot={g}")
    elif kind == "quote":
        g = round(bot.quote(o), 2)
        print(f"  r{ex['round']} pos{o.position:+3d} QUOTE real={act} bot={g:.2f}  {'ok' if act is not None and abs(g-act)<0.02 else ''}")
    else:
        g = bot.respond(o, ex['price'])
        print(f"  r{ex['round']} pos{o.position:+3d} RESP @ {ex['price']:.2f} real={act:+d} bot={g:+d}")
