"""Assemble zoo/arena_paperhands.py: rival_3's opponent inference + PaperHands' decoded policy."""
import sys

R = "/Users/jaiv/Coding/hiddenhand/tqc-hiddenhand-moneyheist"
src = open(R + "/zoo/rival_3.py").read().splitlines()


def lines(a, b):
    """1-indexed inclusive slice of rival_3.py."""
    return "\n".join(src[a - 1:b])


def find(prefix, start=1):
    for i in range(start - 1, len(src)):
        if src[i].startswith(prefix):
            return i + 1
    raise KeyError(prefix)


PARAMS = dict(EDGE=2.05, EDGE_MIN=2.6, NEUTRAL=1.85, PUSH=13.0, PUSH_K=0.9, PUSH_TMIN=0.3,
              ID_CONF=0.9, TAKE_M=1.0, TAKE_M2=2.0, TAKE_POS=0.3, U_TEV=2.2, U_TRUST=0.0)
for kv in sys.argv[2:]:
    k, v = kv.split("=")
    PARAMS[k] = float(v)
out_path = sys.argv[1] if len(sys.argv) > 1 else R + "/zoo/arena_paperhands.py"

HEADER = '''# Team Name: Zoo - arena_paperhands
# Members: Organisers
# Mentor: None

"""
arena_paperhands.py - imitation of arena team "PaperHands" (entry #26, v3),
decoded from its public replays (zoo/arena_raw/paperhands/).

What the replays show, and what this file does:

  * First quote of the deal (no opponent quote yet): the PUBLIC estimate
    (board + 15 - len(board) cards at the public average), 105.00 at the
    start. Its hand never shows in that quote.
  * It identifies the opponent's model and hand exactly. Against naive,
    reader and sharp its quotes sit at the opponent's exact fair value
    +-2.05 (just past their +-2 no-trade band) whenever it wants to trade:
    +2.05 makes them sell to it, -2.05 makes them buy from it. Here the
    identification is rival_3's (a posterior over model x hand sum), and
    P = the predicted opponent fair when it answers.
  * Against readers (they read our quote with a trust) it STEERS: in rounds
    2-3 it quotes up to 13.00 past their fair, against its own interest for
    that one trade, so their next quotes move the wrong way; then in rounds
    4-5 it trades at +-2.05 into their mispriced quotes. A bearish
    PaperHands pushes up (quote = P + 13), a bullish one pushes down.
    Round 2 pushes are partial (about 0.9 x its edge), round 3 is the full 13.
  * Small edge (under ~2.6): a neutral quote just inside the band on its
    own side (P -+ 1.85), so nothing trades.
  * Opponent not identified (hiders, planners, anything odd): it COPIES
    the opponent's last quote. Their own fair value gives them no reason
    to trade against it.
  * As taker: trades when its value is past the price + 2 by TAKE_M
    (2 lots past TAKE_M2).
  * Swap: round 5 only, whenever it holds a position: lowest card when long,
    highest when short. Never peeks.

Parameters below were calibrated so that local results against the house
bots and rival_3 land near the arena scores (naive +9.97, reader +16.92,
sharp +15.39, Alpha Rodeo/rival_3 +2.67).
"""
'''

consts = "\n".join(f"{k} = {v!r}" for k, v in PARAMS.items())

parts = [HEADER,
         lines(find("import math"), find("SQ2 =")),
         "GEN_UNI = 0.3\nTSOLVE = 2.5\nMAXS = 4\nTGRID = (0.15, 0.5, 0.85)\n",
         "# decoded PaperHands policy\n" + consts + "\n",
         lines(find("# (name, kind, trust"), find("K = len(MODELS)")),
         "",
         lines(find("def phi(x):"), find("def schedule(seat):") - 1).rstrip(),
         "",
         "",
         lines(find("class Bot:"), find("    def _t_known(self):") - 1).rstrip(),
         "",
         lines(find("    @staticmethod"), find("    @staticmethod") + 5),
         ]

POLICY = '''
    # ------------------------------------------------------------ PaperHands policy
    def move(self, obs):
        try:
            self._sync(obs)
            if obs.round != 5 or obs.position == 0:
                return None
            if any(w == "me" for _, w, _ in obs.discards):
                return None
            un = obs.unseen
            m = sum((r + 1) * c for r, c in enumerate(un)) / sum(un)
            h = obs.hand
            if obs.position > 0:
                i = min(range(5), key=lambda j: h[j])
                return ("SWAP", i) if h[i] < m else None
            i = max(range(5), key=lambda j: h[j])
            return ("SWAP", i) if h[i] > m else None
        except Exception:
            return None

    def quote(self, obs):
        try:
            return self._quote(obs)
        except Exception:
            return round(self._public(obs), 2)

    def respond(self, obs, price):
        try:
            return self._respond(obs, price)
        except Exception:
            return 0

    @staticmethod
    def _public(obs):
        return public_est(sum(obs.board), len(obs.board),
                          sum(r for _, _, r in obs.discards), len(obs.discards))

    def _view(self, obs, ctx, qlast):
        """(my EV, predicted opponent fair when it answers, identified?, reader trust)."""
        c0, c1 = self._ev_lin(obs)
        samples = self._samples()
        ev = sum(w * (c0 + c1 * s) for w, k, s, t in samples)
        P = 0.0
        for w, k, s, t in samples:
            P += w * their_fair(MODELS[k][1], t, ctx, s, qlast)
        top = max(samples, key=lambda x: x[0])
        ident = MODELS[self.top_k][6] == 1 and self.top_mass >= ID_CONF
        trust = top[3] if MODELS[top[1]][1] == "R" and self._t_known() else 0.0
        return ev, P, ident, trust

    def _t_known(self):
        """Is the main hypothesis' reading trust pinned down by the data?"""
        if MODELS[self.top_k][2] is not None:
            return True
        row = self.J[self.top_k]
        tn = sum(row[i] for i in range(NG) if self.T[i] is not None)
        return tn > 0.95 * sum(row)

    def _value(self, obs, price=None):
        """My value. Identified opponent: the posterior EV. Otherwise their
        quotes are not believed: naive value + U_TRUST x what their latest
        quote implies + U_TEV per lot they bought from my quotes (- per lot sold)."""
        c0, c1 = self._ev_lin(obs)
        samples = self._samples()
        if MODELS[self.top_k][6] == 1 and self.top_mass >= ID_CONF:
            return sum(w * (c0 + c1 * s) for w, k, s, t in samples)
        un = obs.unseen
        m = sum((r + 1) * c for r, c in enumerate(un)) / sum(un)
        hb = 5 - len(obs.board)
        v = sum(obs.hand) + sum(obs.board) + (5 + hb) * m
        theirs = [px for r, w, px, q in obs.tape if w == "opp"]
        if price is not None:
            theirs.append(price)
        if theirs and U_TRUST:
            v += U_TRUST * (theirs[-1] - sum(obs.board) - (10 + hb) * m)
        v += U_TEV * sum(q for r, w, px, q in obs.tape if w == "me")
        return v

    def _quote(self, obs):
        self._sync(obs)
        if self.seat is None:
            self.seat = 0
        ctx = self._ctx(obs)
        qlast = self._last_me(obs.tape)
        j = len(obs.tape)
        self.pending[j] = (ctx, qlast, obs.position)
        theirs = [px for r, w, px, q in obs.tape if w == "opp"]
        if not theirs:
            return round(self._public(obs), 2)
        ev, P, ident, trust = self._view(obs, ctx, qlast)
        if not ident:
            return round(theirs[-1], 2)                  # copy their last quote
        ev = self._value(obs)
        pos = obs.position
        gap = ev - P
        room_buy = pos < LIM
        room_sell = pos > -LIM
        if trust >= PUSH_TMIN and obs.round in (2, 3):
            push = PUSH if obs.round == 3 else min(PUSH, PUSH_K * abs(gap))
            if gap > 0 and room_buy:
                return round(max(0.0, P - push), 2)      # bullish: drag their value down
            if gap < 0 and room_sell:
                return round(min(195.0, P + push), 2)    # bearish: drag it up
        if gap > EDGE_MIN and room_buy:
            return round(P + EDGE, 2)                    # they sell to us at P + 0.05
        if gap < -EDGE_MIN and room_sell:
            return round(P - EDGE, 2)                    # they buy from us at P - 0.05
        if (gap > 0 and not room_buy) or (gap < 0 and not room_sell):
            return round(ev, 2)
        return round(P + (NEUTRAL if gap > 0 else -NEUTRAL), 2)

    def _respond(self, obs, price):
        self._sync(obs)
        if self.seat is None:
            self.seat = 1
        ctx = self._ctx(obs)
        qlast = self._last_me(obs.tape)
        self._obs_quote(ctx, qlast, price)
        self.nq += 1
        self.done_tape.add(len(obs.tape))
        e = self._value(obs, price) - price - TAKE_POS * obs.position
        if e > 2 + TAKE_M2:
            return 2
        if e > 2 + TAKE_M:
            return 1
        if e < -2 - TAKE_M2:
            return -2
        if e < -2 - TAKE_M:
            return -1
        return 0
'''

text = "\n".join(parts) + "\n" + POLICY
open(out_path, "w").write(text)
print("wrote", out_path)
