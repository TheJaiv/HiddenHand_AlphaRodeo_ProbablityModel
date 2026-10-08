"""replay_infer.py BOT TEAM DIR - run BOT's opponent model as an observer on every replay in DIR:
for each play, take the seat facing TEAM, feed the recorded tape round by round into BOT's _sync,
and print P(reader) after rounds 2..5 (BOT must be the rival_2 / hunt line, with _p_reader)."""
import sys, json, glob, statistics as st
from pathlib import Path
KIT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(KIT))
from bot_loader import load_for_testing
from rules import Obs
RK = {'A': 1, 'J': 11, 'Q': 12, 'K': 13}
def rk(s):
    s = s[:-1]; return RK.get(s) or int(s)
botf, team, d = sys.argv[1], sys.argv[2], sys.argv[3]
B = load_for_testing(botf, quiet=True)
rows = []
for f in sorted(glob.glob(f"{d}/*.json")):
    try:
        g = json.load(open(f))
    except Exception:
        continue
    if not isinstance(g, dict) or 'plays' not in g:
        continue
    for p in g['plays']:
        if team not in p['seats']:
            continue
        tseat = p['seats'].index(team)
        me = 1 - tseat
        opp_name = p['seats'][me]
        hand = list(p['hand_ranks'][me]); board = p['board_ranks']
        tape = []; disc = []; peeks = []; pos = 0
        bot = B()
        out = []
        for row in p['rounds']:
            r = row['round']
            for j, mv in enumerate(row['moves']):
                if mv and mv.get('kind') == 'swap':
                    disc.append((r, 'me' if j == me else 'opp', rk(mv['out'])))
                    if j == me:
                        hand.remove(rk(mv['out'])); hand.append(rk(mv['in']))
                elif mv and mv.get('kind') == 'peek':
                    peeks.append((r, 'me' if j == me else 'opp'))
            for q in row['quotes']:
                tape.append((r, 'me' if q['maker'] == me else 'opp', q['price'], q['qty']))
                if q['maker'] == me:
                    pos -= q['qty']
                else:
                    pos += q['qty']
            shown = board[:r - 1]
            unseen = [4] * 13
            for c in hand + shown + [x[2] for x in disc]:
                unseen[c - 1] -= 1
            obs = Obs(round=r, hand=tuple(hand), board=tuple(shown), opp_known=(), unseen=tuple(unseen),
                      position=pos, cash=0.0, spent=0.0, tape=tuple(tape), discards=tuple(disc), peeks=tuple(peeks))
            bot._sync(obs)
            if bot.first is None:
                bot.first = row['quotes'][0]['maker'] == me
            if r >= 2:
                out.append(bot._p_reader()[0])
        rows.append((opp_name, out))
print(f"{team}: {len(rows)} plays; mean P(reader) after rounds 2..5:",
      [round(st.mean(o[k] for _, o in rows), 2) for k in range(4)],
      "; share with P >= 0.85 after r3/r4:", round(sum(o[1] >= 0.85 for _, o in rows) / len(rows), 2),
      round(sum(o[2] >= 0.85 for _, o in rows) / len(rows), 2))
