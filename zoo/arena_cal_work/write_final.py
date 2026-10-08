"""Write zoo/arena_cal_<team>.py (passes) or zoo/arena_cal_work/<team>_attempt.py (fails) from final_<key>.json."""
import json, sys
import build, jfit

NAMES = {"tp": "teenpatti", "qt": "quants_treasure", "cy": "cyberpsycho", "ph": "paperhands",
         "gz": "genz7", "aj": "aj_the_trader"}
LIVE_ID = {"r1": "rival_1 #351", "r2": "rival_2 #368", "h1": "hunt_v01 #383", "h2": "hunt_v02 #393",
           "naive": "house naive", "reader": "house reader", "sharp": "house sharp"}
DECODED = {
 "tp": """Decoded from replays: first quote = naive fair + ~1.6 (104.25 with hand 32, 105.63 after our
round-1 discard of a 2); swaps in round 5; quotes near its own value blended toward the
opponent's last quote; takes trades on its own value (sold into rival_1's 124-138 steering).""",
 "qt": """Decoded from replays: a MIRROR. First quote = public estimate (105.00; 106.47 after our
round-1 discard of a 2), then quotes exactly our last quote, including rival_2's paid probes
80.59 (implied hand 7) and 136.41 (implied hand 63). Never reads quotes for value (trust 0),
learns from our trades on its quotes. Swaps from round 3-4.
NEW: it does NOT copy quotes outside an implied-hand window (MIR_LO..MIR_HI): copying our free
0 / 195 quotes at +-10 lots would hand us ~80 per lot, and it beats rival_2 live by 4.3.""",
 "cy": """Decoded from replays: first quote ~ naive fair + 2.6 (107.62 with hand 32, 109.54 after our
round-1 discard of a 2); blends own value with the opponent's last quote; swaps in round 5.""",
 "ph": """Decoded from replays: first quote = public estimate (105.00; 106.47 after our discard of a 2);
against house bots quotes at their fair +-3.05; heavy trade evidence; swaps in round 5.
NEW (decoded, 5/5 cases): at -10 lots it quotes 0.00 (and 195 at +10) - free, steers readers.
NEW (decoded): ignores our 195 / 179 quotes (replay vs #383).""",
 "gz": """Decoded from replays: first quote = 15 x its own card average (105.96; 107.14 after our
round-1 discard of a 2); bounds its prediction of our value by our trades; swaps in round 5.
NEW (decoded): ignores our 195 quote at +10 lots (replay vs #368: next quotes 119.6, 123.8).""",
 "aj": """Decoded from replays: first quote = public estimate (105.00; 106.47 after our discard of a 2);
against house bots its quotes sit at their exact fair +-2.06; low quote trust, trade evidence;
swaps from round 2-3.
NEW (decoded): ignores our extreme quotes: after rival_2's 136.59 it quotes 116.43 then 121.38
(old imitation: 129.84, 134.46); after our 0.00 it quotes 115.07 (old imitation: 37.16).""",
}
STRUCT = """What the old zoo/arena_* imitations missed: they read EVERY quote of ours linearly (value
read with trust T, and the blend toward 'their last quote' with weight W), so rival_2's free
0 / 195 quotes at +-10 lots and its paid probes (implied hand 7 / 63) steered them by 15-80
points, and rival_2 farmed that. The real teams ignore quotes whose implied hand is outside
[SANE_LO, SANE_HI] (both for their value and for their prediction of ours)."""


def main():
    key = sys.argv[1]
    f = json.load(open(f"final_{key}.json"))
    rows, params, ok = f["rows"], f["params"], f["ok"]
    team = NAMES[key]
    c = jfit.TEAMS[key]
    tab = ["Calibration (local: tools/eval.py OURBOT --vs THIS --deals 500 --seeds 1 2; score from the",
           "side of OUR bot / the house bot; criterion |diff| <= 1.5 on rival_1, rival_2, hunt_v01):",
           f"  {'opponent':16s} {'live':>7s} {'local':>7s} {'+-2se':>6s} {'diff':>6s}"]
    for o, live, loc, e, d, passed, crit, side in rows:
        tab.append(f"  {LIVE_ID[o]:16s} {live:+7.2f} {loc:+7.2f} {e:6.2f} {d:+6.2f}  {'PASS' if passed else 'FAIL'}"
                   f"{'' if crit else ' (extra target)'}")
    fitted = ("Fitted (replay agreement + the live scores above, zoo/arena_cal_work/jfit.py): "
              + ", ".join(f"{k}={v}" for k, v in params.items()
                          if k in ("T", "W", "SKEW_Q", "C_Q", "SKEW_R", "TH1", "TH2", "HIDE", "TRADE_EV",
                                   "TB_G", "TB_F", "SANE_LO", "SANE_HI", "MIR_LO", "MIR_HI", "SWAP_R", "SWAP_G")))
    doc = f"""arena_cal_{team}.py - CALIBRATED imitation of arena team "{c['name']}" (entry #{c['entry']}).

{DECODED[key]}

{STRUCT}

{chr(10).join(tab)}

Replay agreement loss (quote MAE + 6 x response miss rate + 4 x move miss rate, replays vs
our entries weighted x3): {f['tape']:.2f}.
{fitted}
Built on the shared blend core (zoo/arena_cal_work/cal_core.py): F = my value (my hand + board +
their hand read from their sane quotes with trust T + trade evidence), P = their last sane quote
carried forward and bounded by their trades on my quotes; quote = (1-W)(F - SKEW_Q pos) + W P + C_Q.
"""
    path = f"../arena_cal_{team}.py" if ok else f"{team}_attempt.py"
    build.write(path, f"arena_cal_{team}" if ok else f"arena_cal_{team}_attempt", params, doc)
    print("wrote", path)


if __name__ == "__main__":
    main()
