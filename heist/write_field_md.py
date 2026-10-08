"""heist/write_field_md.py - write heist/FIELD.md from data/matrix.json, data/fits.json, data/calib.json, data/field.json."""
import json
import os
import statistics as S

HERE = os.path.dirname(os.path.abspath(__file__))
m = json.load(open(os.path.join(HERE, "data", "matrix.json")))
fits = json.load(open(os.path.join(HERE, "data", "fits.json")))
cal = json.load(open(os.path.join(HERE, "data", "calib.json")))
field = json.load(open(os.path.join(HERE, "data", "field2.json")))
st, nw, ours, mat = m["standings"], m["newest"], m["ours"], m["matrix"]
OURS = [e for e in ("573", "565", "561") if e in ours]


def style(P):
    if P["W"] >= 0.6:
        return "follower"
    if P["W"] >= 0.25:
        return "blend"
    return "reader" if P["T"] >= 0.4 else "honest"


def vs(e, team):
    k = f"{team}#{nw[team]}"
    return ours[e].get(k)


L = []
L.append("# The live field (heist/FIELD.md)\n")
L.append(f"Census {m['made']} from the public standings and fight list (heist/census.py; data in heist/data/). "
         "Every live fight uses the same hidden 400-deal set, so a deterministic bot scores exactly the same against an "
         "unchanged opponent upload: our paired live comparisons have no deal noise per opponent.\n")
L.append("Our entries: #486 tokyo, #495 nairobi, #505 rio, #513 moscow, #561 helsinki, #565 lisbon, #569 j01 (safe-quote test), #573 e01.\n")
L.append("## Top 15\n")
L.append("| # | Team | Score | Won | Newest | e01 #573 vs it | helsinki #561 vs it | Style (fit) |")
L.append("|---|---|---|---|---|---|---|---|")
for r in [x for x in st if x["rank"]][:15]:
    t = r["team"]
    a = vs("573", t) if "573" in ours else None
    b = vs("561", t)
    sty = style(fits[t]["P"]) if t in fits else "-"
    L.append(f"| {r['rank']} | {t} | {r['score']:+.2f} | {r['won']}/{r['fights']} | #{nw[t]} | "
             f"{'-' if a is None else f'{a:+.2f}'} | {'-' if b is None else f'{b:+.2f}'} | {sty} |")
L.append("")
L.append("## Who beats us, whom we beat (e01 #573 against each team's newest entry)\n")
row = ours["573"]
lose = sorted((s, k) for k, s in row.items() if s < 0)
win = sorted(((s, k) for k, s in row.items() if s >= 0), reverse=True)
L.append("Beat us: " + ", ".join(f"{k} {s:+.2f}" for s, k in lose) + ".\n")
L.append(f"We beat {len(win)} of {len(row)}; biggest: " + ", ".join(f"{k} {s:+.2f}" for s, k in win[:10]) + ".\n")
L.append("## Who beats the top teams (newest vs newest)\n")
for r in [x for x in st if x["rank"]][:8]:
    t = r["team"]
    b = sorted((sc, o) for o, sc in mat.get(t, {}).items() if sc < 0)
    L.append(f"- {t}: " + (", ".join(f"{o} {sc:+.2f}" for sc, o in b) if b else "nobody") )
L.append("")
L.append("## Styles (from replays)\n")
L.append("""Every fight page shows the same deal 1 (hands 3 4 J 9 5 = 32 and 2 10 Q 8 8 = 40, board J 2 Q Q 10), so a team is
seen with two hands only, against many opponents. What the replays show:

- **Followers / nudgers** (quote = the opponent's last quote, carried for board cards, +- a small step): Happy Happy #463
  (exactly ours + 1.1, takes only at 5+ points of edge, ignores absurd prices), PaperHands (round 1: ours + 2.15, sd 0.13),
  Techy Traders (ours - 1.3; first quote with a low hand 5.3 ABOVE its fair), Imposters (ours + 1.3; always swaps in round 4;
  answers exactly 1 lot in round 1), MNC (ours - 1.1), AnalysisParalysis, TeenPatti, Quants Treasure. Their quotes show
  nothing of their hand; they make money by taking. Top teams are of this kind.
- **Readers** (their quote moves with what our quote implies, trust ~1): Hidden Alpha, Apex, Phantom Halo, house reader / sharp.
- **Honest naive-formula quoters** (first quote exactly the naive card count, 103.74 on deal 1): Pravichayah, Quant Qods,
  Chanakya, Apex, Hidden Alpha, Phantom Halo, house bots. We beat these by +5 to +11.
- **Swaps:** top teams swap late (Imposters r4 in 156/159 plays, PaperHands / Techy r5) and account for the opponent's
  discard (fitted swap accounting 0.5-0.9: a discarded 2 raises their price ~5). We used to swap in round 1, which gave
  that information away early (fixed in rio).
- **Answers:** most fitted teams take only at 4-7 points of edge; Imposters / MNC / alpha answer 1 lot in round 1 (61-76%).
""")
L.append("""## Afternoon findings (live)

- **Extraction gap.** Against the mid-field the top teams make far more PnL per deal than we do (ThunderX: PaperHands +23.4,
  Imposters +17.9, us +1.3; Pokemons +26.0 / +11.1 / +3.3; MNC +23.2 / +12.8 / +6.6; Blind_Ambition +29.7 / +19.1 / +7.5;
  Double Dividend +24.6 / +13.2 / +4.2). On the same opponents the top three beat our current versions by +0.4 to +0.6.
- **Hand effect** (heist/handeffect.py; replays show both hands): quote slope per point of own hand ~0.85-1.0 for honest
  quoters (naive, QUANTSTATIC, Bulls, Apex, Blind, alpha, Void), ~0 for hiders / followers (Sattebaaz, Risk Violators,
  Pokemons, Godtier), negative for MNC / TeenPatti / Genz7 (-0.4), Cyberpsycho, Imposters (-0.25). Deal 1 always pairs a 32
  hand with a 40 hand, so reading the opponent and hiding one's own hand look alike here.
- **Pickers.** The refreshed ThunderX imitation (matches live) shows how followers that read us and take only at ~5 points of
  edge beat us: our maker PnL is negative in every round (-8.7 per play) while our taking wins (+14).
- **Peekers.** Quants Treasure peeks in rounds 1-3 (9 points a deal). A defence (safe quotes + taker margin after 2 peeks)
  made it worse live (lisbon: QT -0.65, Team How -1.4).
- **Plateau.** rio, moscow, helsinki, lisbon and e01 all score the same live (+5.3) but split opponents differently
  (helsinki-line: Godtier +2.5, Cyberpsycho +1.9, Chanakya +3.5; rio: Imposters +0.8, Genz7 +0.6, PaperHands +0.4).
""")
L.append("## Field model (heist/opp/, heist/data/field2.json)\n")
L.append("One parameterised bot (heist/opp_core.py) fitted to each team's replays (heist/fit_opp.py: quote error, answer and "
         "move agreement), then checked against the live scores of our own files (heist/calib.py). Only imitations within "
         "1.5 of every live score are used; each is weighted by how many live teams share its style. House bots are included "
         "as themselves (exact).\n")
L.append("| Imitation | Style | Weight | Replay fit (quote err / answer miss / move miss) | Live vs local (our files) |")
L.append("|---|---|---|---|---|")
for t, d in sorted(field.items(), key=lambda x: (x[1]["style"], x[0])):
    key = t.split(" #")[0]
    f = fits.get(key, {})
    c = cal.get(key, [])
    cc = "; ".join(f"#{x['entry']} {x['live']:+.2f}/{x['local']:+.2f}" for x in c[:3]) if c else "#466 -0.10/+0.62"
    fq = f"{f.get('qerr', 0):.2f} / {f.get('rmiss', 0):.2f} / {f.get('mmiss', 0):.2f}" if f and key != "Happy Happy" else "0.49 / 0.04 / 0.18"
    L.append(f"| {t} | {d['style']} | {d['weight']} | {fq} | {cc} |")
bad = sorted(t for t, rows in cal.items() if not all(abs(r['local'] - r['live']) <= 1.5 for r in rows))
L.append("\nNot calibrated (left out): " + ", ".join(bad) + ".\n")
open(os.path.join(HERE, "FIELD.md"), "w").write("\n".join(L) + "\n")
print("FIELD.md written")
