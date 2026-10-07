"""
tools/trace.py - watch one bot think through ONE deal (local only)
==================================================================

Never uploaded, never changes a bot. It plays one deal with engine.play_deal
and, after every move / quote / respond call BOT makes, prints what BOT
returned, the truth (the opponent's real hand sum, the real final value V)
and what BOT believed at that moment, read from BOT's own attributes.

    python tools/trace.py BOT OPP                     seed 1, deal 0, BOT in seat 0
    python tools/trace.py BOT OPP --seed 3 --deal 7   deal 7 of play_match(seed=3)
    python tools/trace.py BOT OPP --swap              same cards, seats swapped (BOT in seat 1)

BOT and OPP are paths or house bot names (naive, reader, sharp), as in backtester.py.

What is read depends on which attributes BOT has:
    self.hyps   rival_1 style: exact hypotheses about the opponent's pricing rule
    self.H      rival_2 style: weighted Bayesian hypotheses
A bot with neither only gets the truth lines.

How the truth is known in advance: the deal is played twice. The first,
silent play gives the final value V and every swap; the second play, with the
same seeds, is the one printed. Both plays seed Python's shared `random`
module exactly as eval.py does for that game, so they come out identical (the
tool says so if they do not).

Read-only: every read happens on a deep copy of the bot, taken right after its
call returns, so even a helper that writes to self (rival_1's _state sets
self.t_eff) cannot change the real bot. The wrapper also reports only the real
call's time to the engine, so the printing never counts towards the 50 ms limit.
"""

from __future__ import annotations

import argparse
import copy
import math
import random
import sys
import time
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent      # the folder holding engine.py
sys.path.insert(0, str(KIT))

from backtester import describe, resolve            # noqa: E402  (kit files, used as they are)
from bot_loader import load_for_testing             # noqa: E402
from engine import derive_seed, play_deal, rank     # noqa: E402


# ── The truth, from the silent play's log ───────────────────────────

def true_hand_sum(log: dict, seat: int, rnd: int, swaps_done: bool) -> int:
    """Real hand sum of `seat` during round rnd.

    Moves come before quotes in a round, so a move call sees the hand before
    this round's swap (swaps_done=False) and a quote / respond call after it.
    """
    total = sum(rank(c) for c in log["hands"][seat])       # the hand as dealt
    for row in log["rounds"]:
        mv = row["moves"][seat]
        happened = row["round"] < rnd or (swaps_done and row["round"] == rnd)
        if happened and mv and mv["kind"] == "swap":
            total += rank(mv["in"]) - rank(mv["out"])
    return total


# ── What BOT believed: rival_1 style (self.hyps) ────────────────────

def rival1_lines(bot, obs, method: str, out, opp_now: int, V: int) -> float:
    """Print rival_1's state. Returns its E (expected final value)."""
    # A hypothesis is (trust, my cards they peeked, their hand sum S, their pending discard).
    trusts = sorted({h[0] for h in bot.hyps})
    print(f"   hyps {len(bot.hyps)} (trust {', '.join(f'{t:g}' for t in trusts)})   dead {bot.dead}")

    best = bot._best()                      # None until a quote of theirs pins S down
    E, hyp, S, var, pm = bot._state(obs)    # S here is adjusted for a swap they made since
    if best is None:
        print(f"   best: none (not identified, Gaussian fallback)   S {S:.1f} +- {math.sqrt(max(var, 0.0)):.1f}"
              f"  (true {opp_now})")
    else:
        swapped = f", then they swapped out a {best[3]}" if best[3] else ""
        print(f"   best: trust {best[0]:g}, S {best[2]}{swapped}   S now {S:.1f}  (true {opp_now})")
    print(f"   E {E:.2f}  (true V {V}, E - V = {E - V:+.2f})")

    if method == "quote" and isinstance(out, (int, float)):
        F = bot._their_F(obs, hyp, S)[0]    # their fair when they answer this quote
        gap = out - F
        if hyp is None:
            seen = any(e[0] in ("q", "m") for e in bot.ev)    # any quote yet, theirs or mine?
            kind = "FALLBACK quote" if seen else "OPENING quote (as if my hand were average)"
        elif abs(gap) < 2:                  # they trade only beyond 2 from their fair
            kind = "STEER: no trade expected, pulls their fair " + ("down" if gap < 0 else "up")
        else:
            kind = "HARVEST: they should " + ("sell to me" if gap > 0 else "buy from me")
        print(f"   {kind}   (quote - their F {F:.2f} = {gap:+.2f})")
    return E


# ── What BOT believed: rival_2 style (self.H) ───────────────────────

def rival2_lines(bot, obs, method: str, out, opp_now: int, V: int) -> float:
    """Print rival_2's state. Returns its E (expected final value)."""
    # The bot file's own module-level names (H_MO, RAW, MAXP, ...). Every
    # function remembers the module it was written in, so borrow them from
    # __init__. That way this still works if the bot adds a field.
    g = type(bot).__init__.__globals__
    READS, RULE, LAM, TAU, KAP = g["H_READS"], g["H_RULE"], g["H_LAM"], g["H_TAU"], g["H_KAP"]
    MO, MT, LW = g["H_MO"], g["H_MT"], g["H_LW"]
    rule_name = {g[n]: n.lower() for n in ("RAW", "CLAMP", "SANE", "CUR")}

    H = sorted(bot.H, key=lambda h: -h[LW])                  # heaviest first
    total = sum(math.exp(h[LW]) for h in H)                   # LW is a log weight
    print(f"   hyps {len(H)}, top 3:")
    for i, h in enumerate(H[:3], 1):
        print(f"     #{i} {math.exp(h[LW]) / total:4.0%}  reads {'yes' if h[READS] else 'no '}"
              f"  rule {rule_name[h[RULE]]:<5} lam {h[LAM]:.1f}  tau {h[TAU]:.1f}  kap {h[KAP]:.1f}"
              f"   H_MO {h[MO]:5.1f}  H_MT {h[MT]:.2f}")

    mo = bot._mo()                          # weighted mean of their hand sum O
    p_rd, p_raw = bot._p_reader()
    alpha, beta = bot._ev(obs)              # E[V | O] = alpha + beta * O
    E = alpha + beta * mo
    print(f"   _mo {mo:.1f}  (true {opp_now})   _p_reader {p_rd:.2f}, raw {p_raw:.2f}")
    print(f"   E = {alpha:.2f} + {beta:.3f} * {mo:.1f} = {E:.2f}  (true V {V}, E - V = {E - V:+.2f})")

    if method == "quote" and isinstance(out, (int, float)):
        # As in rival_2's _quote: imp0 is the quote that would imply a hand of 0,
        # so (quote - imp0) is the hand sum this quote tells a reader I hold.
        st = bot._state(obs, obs.round, bot.obar)
        imp0 = st[0] + (5 + st[1]) * st[6]
        told = out - imp0
        if out >= g["MAXP"] - 1e-9 or out <= 1e-9:
            kind = "EXTREME (195 / 0)"
        elif any(abs(told - k) < 0.01 for k in (63, 7, 55, 15)):
            kind = "PROBE"
        elif any(abs(told - k) < 0.01 for k in (65, 58, 5, 12)):
            kind = "EXTREME at the position limit (edge of what clamp / sane readers believe)"
        else:
            kind = "normal"
        print(f"   {kind} quote: tells a reader my hand is {told:.1f}  (it is {sum(obs.hand)})")
    return E


# ── The wrapper ─────────────────────────────────────────────────────

def show_move(out, obs) -> str:
    if out is None:
        return "pass"
    if isinstance(out, (tuple, list)) and len(out) == 2 and out[0] == "SWAP":
        return f"SWAP slot {out[1]} (a {obs.hand[out[1]]})"
    return str(out)                         # "PEEK", or something the engine will reject


class Traced:
    """Passes every call through to BOT unchanged, then prints a report."""

    def __init__(self, bot, me: int, log: dict):
        self.bot = bot
        self.me = me                        # BOT's seat, 0 or 1
        self.log = log                      # the silent play's log: the truth
        self.last_call_ms = None            # read by the engine (see _call)

    def _call(self, method: str, obs, *args):
        t0 = time.perf_counter()
        try:
            out = getattr(self.bot, method)(obs, *args)
        except Exception as e:
            print(f"\nr{obs.round} {method}: CRASHED {type(e).__name__}: {e}  (the engine uses its fallback)")
            raise
        # The engine times this wrapper; tell it the real call's time instead.
        own = getattr(self.bot, "last_call_ms", None)          # a bot may time itself
        self.last_call_ms = own if own is not None else (time.perf_counter() - t0) * 1000
        self.report(method, obs, args, out, copy.deepcopy(self.bot))
        return out

    def move(self, obs):
        return self._call("move", obs)

    def quote(self, obs):
        return self._call("quote", obs)

    def respond(self, obs, price):
        return self._call("respond", obs, price)

    def report(self, method: str, obs, args: tuple, out, probe) -> None:
        """probe is a deep copy of BOT: read it freely, the real bot never sees it."""
        opp_now = true_hand_sum(self.log, 1 - self.me, obs.round, swaps_done=method != "move")
        V = self.log["V"]
        if method == "move":
            what = show_move(out, obs)
        elif method == "quote":
            what = f"quotes {out:.2f}" if isinstance(out, (int, float)) else f"quotes {out!r}"
        else:
            what = f"answers {args[0]:.2f} with {out:+d}" if isinstance(out, int) else f"answers {out!r}"
        print(f"\nr{obs.round} {method:<7}  {what:<32} pos {obs.position:+d}   "
              f"TRUE: opp hand {opp_now}, V {V}")

        E = None
        try:
            if hasattr(probe, "hyps"):
                E = rival1_lines(probe, obs, method, out, opp_now, V)
            elif getattr(probe, "H", None):
                E = rival2_lines(probe, obs, method, out, opp_now, V)
        except Exception as e:              # a reading problem must never stop the deal
            print(f"   (could not read BOT's state: {type(e).__name__}: {e})")
        if method == "respond" and E is not None:
            print(f"   E - price = {E - args[0]:+.2f}  (buying costs price + 2, selling gets price - 2)")


# ── Main ────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Hidden Hand: trace one bot through one deal")
    ap.add_argument("bot")
    ap.add_argument("opp")
    ap.add_argument("--seed", type=int, default=1, help="match seed, as in eval.py / backtester.py")
    ap.add_argument("--deal", type=int, default=0, help="deal number inside that match")
    ap.add_argument("--swap", action="store_true", help="the mirrored game: same cards, BOT in seat 1")
    args = ap.parse_args()

    bot_path, opp_path = resolve(args.bot), resolve(args.opp)
    names = (bot_path.stem, opp_path.stem if opp_path.stem != bot_path.stem else opp_path.stem + "2")
    bot_cls = load_for_testing(bot_path, quiet=True)
    opp_cls = load_for_testing(opp_path, quiet=True)

    me = 1 if args.swap else 0                              # BOT's seat
    deal_seed = derive_seed(args.seed, args.deal)           # how play_match seeds deal D
    rng_seed = derive_seed(args.seed, "rng", 2 * args.deal + me)   # how eval.py seeds `random` for it

    def play(wrap=None) -> dict:
        random.seed(rng_seed)
        bot, opp = bot_cls(), opp_cls()                     # BOT built first, as in eval.py
        if wrap:
            bot = wrap(bot)
        if me == 0:
            return play_deal(bot, opp, deal_seed, names=names)
        return play_deal(opp, bot, deal_seed, names=names[::-1])

    silent = play()
    log = silent["log"]
    print(f"{names[0]} (BOT, seat {me}) vs {names[1]} (seat {1 - me}), "
          f"seed {args.seed}, deal {args.deal}{', swapped' if args.swap else ''}")
    print(f"TRUE final value V = {log['V']}; hands as dealt: {names[0]} "
          f"{sum(rank(c) for c in log['hands'][me])}, {names[1]} {sum(rank(c) for c in log['hands'][1 - me])}")

    traced = play(lambda b: Traced(b, me, log))
    if traced["pnl"] != silent["pnl"]:
        print("\n! the traced play differs from the silent one (a bot uses an unseeded "
              "random.Random()?), so the TRUE numbers above may be wrong")
    for who, notes in zip(traced["log"]["names"], traced["notes"]):
        for msg, k in notes.items():
            print(f"! {who}: {msg}  (x{k})")

    print("\n=== replay ===")
    print(describe(traced["log"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
