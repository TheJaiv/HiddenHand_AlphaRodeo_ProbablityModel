"""Feed every recorded situation of a team into a bot (teacher forcing) and compare actions.

    python fidelity.py BOT.py TEAM_DIR "Team Name" [ENTRY_ID] [-v]
"""
import importlib.util
import sys
from collections import defaultdict

import tapes


def load_bot(path):
    spec = importlib.util.spec_from_file_location("botmod_" + str(abs(hash(path))), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.Bot


def run(bot_path, team_dir, team, entry=None, verbose=False):
    Bot = load_bot(bot_path)
    stats = defaultdict(lambda: [0, 0])
    qerr = []
    cur_key, bot = None, None
    rows = []
    for kind, o, act, ex in tapes.team_decisions(team_dir, team, entry):
        key = (ex["fight"], ex["seat"])
        if key != cur_key:
            cur_key, bot = key, Bot()
        if kind == "move":
            got = bot.move(o)
            if isinstance(got, list):
                got = tuple(got)
            ok = got == act
        elif kind == "quote":
            got = round(float(bot.quote(o)), 2)
            ok = act is not None and abs(got - act) <= 0.011
            if act is not None:
                qerr.append(abs(got - act))
        else:
            got = int(bot.respond(o, ex["price"]))
            # the engine clamps to the position limit; compare clamped values
            L = 10
            pos = o.position
            got = max(-L - pos, min(got, L - pos))
            ok = got == act
        stats[kind][0] += ok
        stats[kind][1] += 1
        rows.append((ok, kind, ex, act, got, o))
        if verbose and not ok:
            print(f"  MISS {ex['fight']:<34} seat{ex['seat']} r{ex['round']} {kind:<7} "
                  f"real={act} bot={got}" + (f" @ {ex['price']}" if kind == "respond" else ""))
    tot_ok = sum(v[0] for v in stats.values())
    tot = sum(v[1] for v in stats.values())
    line = "  ".join(f"{k}: {v[0]}/{v[1]}" for k, v in stats.items())
    mq = sum(qerr) / len(qerr) if qerr else 0
    print(f"{bot_path.split('/')[-1]} on {team}{' #' + str(entry) if entry else ''}: {tot_ok}/{tot} exact  ({line})"
          f"  mean |quote err| {mq:.2f}")
    return rows


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "-v"]
    entry = int(args[3]) if len(args) > 3 else None
    run(args[0], args[1], args[2], entry, "-v" in sys.argv)
