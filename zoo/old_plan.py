# Team Name: Zoo old_plan
# Members: Organisers' house bots, extended by the old Wednesday roadmap
# Mentor: None

"""
old_plan.py - what the ORIGINAL Wednesday roadmap (Solo Roadmap S6-S10) produces.

A test opponent only: it shows how far "sharp plus careful fixes" gets. It is
strategies/sharp.py with the Wednesday experiments, each behind a switch, and
the switches set to what the experiment loop kept.

KEPT (weighted pool score -7.37 as sharp, +4.42 at the end; 300 deals x seeds 1 2):
  6a +0.37, 6b +0.50, 6c +0.46, 6d +1.67, 7 (T_ME 1.0) +5.48, 8a +2.07,
  9a (gain 30, from round 3) +0.21, 9b +0.39, 10b (noise 0.5) +0.42, 10c (skew 0.2) +0.22
DROPPED: 8b trust adaptation, 9c peeking, 10a shading (not significant or hurt).
Decision rule used: keep if the weighted gain beats 2 standard errors and no single
opponent drops by more than 2.5 (the stricter 0.3 rule kept almost nothing: +0.05).

  S6a  respond() uses the price it is answering as the newest opponent quote
  S6b  each opponent quote is inverted with the board as it was at that time
  S6c  an opponent swap after their last quote shifts their hand by (m - card)
  S6d  every opponent quote is used, newer ones weighted more
  S7   level-2 reading: remove the echo (their quote contains their view of us)
  S8a  their buys / sells / passes on our quotes become bounds on their hand
  S8b  trust drops each time their trades contradict their own quotes
  S9a  swap on the expected final position
  S9b  expect the opponent's swap
  S9c  peek policy
  S10a quote shaded toward the public estimate
  S10b noise on the quote
  S10c inventory skew near the position limit
"""

import random

# ── switches (set by the experiment loop) ─────────────────────────────
USE_PRICE = True      # S6a
BOARD_THEN = True     # S6b
OPP_SWAP_ADJ = True   # S6c
ALL_QUOTES = True     # S6d
LEVEL2 = True         # S7
BOUNDS = True         # S8a
ADAPT_TRUST = False    # S8b
SWAP_FINAL = True     # S9a
EXPECT_OPP_SWAP = True  # S9b
PEEK = 'never'        # S9c: "never" | "r1" | "lowtrust"
SHADE_W = 0.0         # S10a
NOISE = 0.5           # S10b
SKEW = 0.2            # S10c

# ── numbers ───────────────────────────────────────────────────────────
TRUST = 0.8           # how far to move from the prior toward what their quotes imply
T_ME = 1.0            # S7: the trust we assume THEY put in our quotes
DECAY = 0.6           # S8b: trust multiplier per contradiction
FLOOR = 0.1
SWAP_EDGE = 3         # sharp's swap rule (when SWAP_FINAL is off)
SWAP_GAIN = 30.0      # S9a: min expected gain (lots x points) to swap
SWAP_FROM = 3         # S9a: earliest round to swap
OPP_SWAP_K = 0.5      # S9b: scale of the expected opponent swap
LOT_PER_TICK = 1


class Bot:
    # ── small helpers ─────────────────────────────────────────────────
    @staticmethod
    def avg(obs):
        return sum((r + 1) * c for r, c in enumerate(obs.unseen)) / sum(obs.unseen)

    @staticmethod
    def public(obs):
        """Value anyone can see: board + every other card at the public average."""
        ds = sum(c for _, _, c in obs.discards)
        nb, nd = len(obs.board), len(obs.discards)
        return sum(obs.board) + (15 - nb) * (364 - sum(obs.board) - ds) / (52 - nb - nd)

    @staticmethod
    def board_then(obs, r):
        """(board sum, hidden board cards) when a round-r quote was made."""
        if not BOARD_THEN:
            return sum(obs.board), 5 - len(obs.board)
        return sum(obs.board[:r - 1]), 5 - (r - 1)

    def view_of_me(self, obs, upto, m):
        """S7: ffa reader's estimate of MY hand, from my quotes before tape index upto."""
        if not LEVEL2:
            return 5 * m
        last = None
        for j in range(min(upto, len(obs.tape))):
            r, who, px, q = obs.tape[j]
            if who == "me":
                last = (r, px)
        if last is None:
            return 5 * m
        b, hb = self.board_then(obs, last[0])
        implied = last[1] - b - (5 + hb) * m
        return 5 * m + T_ME * (implied - 5 * m)

    def swap_shift(self, obs, r, m):
        """S6c: their hand change from swaps made after round r."""
        if not OPP_SWAP_ADJ:
            return 0.0
        return sum(m - c for rd, who, c in obs.discards if who == "opp" and rd > r)

    # ── the opponent's hand ───────────────────────────────────────────
    def opp_hand(self, obs, new_quote=None):
        m = self.avg(obs)
        prior = sum(obs.opp_known) + (5 - len(obs.opp_known)) * m
        tape = list(obs.tape)
        if new_quote is not None and USE_PRICE:
            tape.append((obs.round, "opp", new_quote, 0))

        # S8b: trust falls when their trades contradict their own quotes
        trust = TRUST
        if ADAPT_TRUST:
            last_q = None
            for r, who, px, q in tape:
                if who == "opp":
                    last_q = px
                elif last_q is not None and ((last_q > px + 2 and q < 0) or (last_q < px - 2 and q > 0)):
                    trust = max(FLOOR, trust * DECAY)

        # S6/S7: implied hand from each of their quotes
        imps = []
        for j, (r, who, px, q) in enumerate(tape):
            if who != "opp":
                continue
            b, hb = self.board_then(obs, r)
            h = px - b - self.view_of_me(obs, j, m) - hb * m
            imps.append(h + self.swap_shift(obs, r, m))
        est = prior
        if imps:
            if ALL_QUOTES:
                ws = range(1, len(imps) + 1)
                implied = sum(w * x for w, x in zip(ws, imps)) / sum(ws)
            else:
                implied = imps[-1]
            est = prior + trust * (implied - prior)

        # S8a: their answers to my quotes bound their hand
        if BOUNDS:
            lo, hi = 5.0, 65.0
            pos = 0                                   # my position before each entry
            for j, (r, who, px, q) in enumerate(obs.tape):
                if who == "me":
                    opp_pos = -pos
                    b, hb = self.board_then(obs, r)
                    rest = b + self.view_of_me(obs, j, m) + hb * m - self.swap_shift(obs, r, m)
                    if q > 0:
                        lo = max(lo, px + 2 - rest)
                    elif q < 0:
                        hi = min(hi, px - 2 - rest)
                    else:
                        if opp_pos < 10:              # they could have bought, so fair <= px + 2
                            hi = min(hi, px + 2 - rest)
                        if opp_pos > -10:             # they could have sold, so fair >= px - 2
                            lo = max(lo, px - 2 - rest)
                    pos -= q
                else:
                    pos += q
            if lo <= hi:
                est = min(hi, max(lo, est))
        return est

    def expected_opp_swap(self, obs, m):
        """S9b: expected value change from a sharp-style opponent swap still to come."""
        if not EXPECT_OPP_SWAP or obs.round >= 5 or obs.position == 0:
            return 0.0
        if any(who == "opp" for _, who, _ in obs.discards):
            return 0.0
        pool = sorted(r + 1 for r, c in enumerate(obs.unseen) for _ in range(c))
        n = len(pool)
        if obs.position < 0:          # they are long: they throw a low card, value rises
            card = pool[n // 6]
            return OPP_SWAP_K * (m - card) if m - card > 3 else 0.0
        card = pool[(5 * n) // 6]     # they are short: they throw a high card, value falls
        return OPP_SWAP_K * (m - card) if card - m > 3 else 0.0

    def fair(self, obs, new_quote=None):
        m = self.avg(obs)
        hidden_board = 5 - len(obs.board)
        return (sum(obs.hand) + sum(obs.board) + self.opp_hand(obs, new_quote)
                + hidden_board * m + self.expected_opp_swap(obs, m))

    def trust_now(self, obs):
        trust, last_q = TRUST, None
        for r, who, px, q in obs.tape:
            if who == "opp":
                last_q = px
            elif last_q is not None and ((last_q > px + 2 and q < 0) or (last_q < px - 2 and q > 0)):
                trust = max(FLOOR, trust * DECAY)
        return trust

    # ── the three calls ───────────────────────────────────────────────
    def move(self, obs):
        try:
            return self._move(obs)
        except Exception:
            return None

    def quote(self, obs):
        try:
            return self._quote(obs)
        except Exception:
            m = self.avg(obs)
            return sum(obs.hand) + sum(obs.board) + (10 - len(obs.board)) * m

    def respond(self, obs, price):
        try:
            return self._respond(obs, price)
        except Exception:
            return 0

    def _move(self, obs):
        swapped = any(who == "me" for _, who, _ in obs.discards)
        if PEEK == "r1" and obs.round == 1:
            return "PEEK"
        if PEEK == "lowtrust" and obs.round <= 3 and self.trust_now(obs) < 0.5 and len(obs.opp_known) < 2:
            return "PEEK"
        if swapped:
            return None
        m = self.avg(obs)
        hand = obs.hand
        if not SWAP_FINAL:            # sharp's rule
            lo = min(range(5), key=lambda i: hand[i])
            hi = max(range(5), key=lambda i: hand[i])
            if obs.position > 0 and hand[lo] < m - SWAP_EDGE:
                return ("SWAP", lo)
            if obs.position < 0 and hand[hi] > m + SWAP_EDGE:
                return ("SWAP", hi)
            return None
        if obs.round < SWAP_FROM:
            return None
        opp_q = [px for r, who, px, q in obs.tape if who == "opp"]
        edge = self.fair(obs) - (opp_q[-1] if opp_q else self.public(obs))
        rounds_left = 5 - obs.round + 1
        step = 1 if edge > 0 else (-1 if edge < 0 else 0)
        final = max(-10, min(10, obs.position + rounds_left * 2 * step))
        best_i = max(range(5), key=lambda i: final * (m - hand[i]))
        if final * (m - hand[best_i]) > SWAP_GAIN:
            return ("SWAP", best_i)
        return None

    def _quote(self, obs):
        q = self.fair(obs)
        if SHADE_W:
            q -= SHADE_W * (q - self.public(obs))
        if SKEW and abs(obs.position) >= 6:
            q -= SKEW * obs.position
        if NOISE:
            q += random.uniform(-NOISE, NOISE)
        return q

    def _respond(self, obs, price):
        edge = self.fair(obs, price) - price
        lots = int((abs(edge) - 2) * LOT_PER_TICK) + 1 if abs(edge) > 2 else 0
        return min(2, lots) * (1 if edge > 0 else -1) 