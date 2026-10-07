# Team Name: Zoo - mid_guard
# Members: AI
# Mentor: None

"""
mid_guard.py - a defensive mid-tier bot: hard to read, careful with information.

  * Quoting: never quote my own fair value. I quote what I think the OPPONENT
    believes the stock is worth (public info + my read of their hand), skewed a
    little towards my side, plus +-0.5 noise. My quote says little about my cards.
  * Reading: reader-style inversion of their latest quote (trust 0.6), then
    clipped by bounds from how they answered my quotes (buy / sell / pass).
  * Moves: peek once (round 2, after their first quote) if that quote looked
    uninformative; swap low when the expected final position is long, high when short.
  * Taking: 2 lots for edge > 3, 1 lot for edge in (2, 3].
"""

import random

TRUST = 0.6          # how far to move from an average hand towards what their quote implies
SKEW_K = 0.5         # share of my edge (vs their view) leaked into my quote
SKEW_MAX = 3.0       # never skew my quote further than this from their view
NOISE = 0.5          # uniform noise added to every quote
SPREAD = 2.0         # taker trades at price +- 2
LIMIT = 10           # position limit
PEEK_TOL = 1.0       # their R1 quote this close to the public estimate = uninformative
SWAP_GAP = 3.0       # only swap a card at least this far from the average unseen rank
BOUND_SLACK = 1.0    # loosen trade bounds a bit: opponents' thresholds differ


class Bot:
    def __init__(self):
        self.rng = random.Random()

    # ---------- public numbers ----------
    def avg(self, obs):
        """Average rank of the cards I have not seen."""
        return sum((r + 1) * c for r, c in enumerate(obs.unseen)) / sum(obs.unseen)

    def implied_hand(self, obs, rnd, fair, m):
        """Invert 'fair = their hand + board + 5 other unknown + hidden board at avg'."""
        board = sum(obs.board[:rnd - 1])
        hidden = 5 - (rnd - 1)
        return fair - board - (5 + hidden) * m

    # ---------- reading the opponent ----------
    def opp_hand(self, obs):
        """Estimate of the sum of the opponent's 5 cards right now."""
        m = self.avg(obs)
        est = sum(obs.opp_known) + (5 - len(obs.opp_known)) * m
        # Their swap: quotes from rounds before it describe a different hand.
        swap_r = max([r for r, who, _ in obs.discards if who == "opp"], default=0)
        swap_shift = 0.0
        for r, who, c in obs.discards:
            if who == "opp":
                swap_shift = m - c        # expected change in their hand from the swap

        # 1) their latest quote, reader-style
        theirs = [(r, px) for r, who, px, q in obs.tape if who == "opp"]
        if theirs:
            r, px = theirs[-1]
            implied = self.implied_hand(obs, r, px, m)
            if r < swap_r:                # quoted before their swap (moves precede quotes)
                implied += swap_shift
            est += TRUST * (implied - est)

        # 2) bounds from their answers to my quotes (walk the tape for their position)
        lo, hi = -1e9, 1e9
        opp_pos = 0
        for r, who, px, q in obs.tape:
            if who == "opp":
                opp_pos -= q              # I was the taker
                continue
            shift = swap_shift if r < swap_r else 0.0
            base = self.implied_hand(obs, r, px, m) + shift
            if q > 0:                     # they bought: their fair > px + 2
                lo = max(lo, base + SPREAD - BOUND_SLACK)
            elif q < 0:                   # they sold: their fair < px - 2
                hi = min(hi, base - SPREAD + BOUND_SLACK)
            else:                         # passed: within +-2, unless blocked by the limit
                if opp_pos < LIMIT:
                    hi = min(hi, base + SPREAD + BOUND_SLACK)
                if opp_pos > -LIMIT:
                    lo = max(lo, base - SPREAD - BOUND_SLACK)
            opp_pos += q
        if lo <= hi:                      # contradictory bounds: ignore them
            est = min(max(est, lo), hi)
        return est

    def fairs(self, obs):
        """(my fair value, my estimate of the opponent's fair value)."""
        m = self.avg(obs)
        board = sum(obs.board)
        hidden = 5 - len(obs.board)
        oh = self.opp_hand(obs)
        mine = sum(obs.hand) + board + oh + hidden * m
        # Their view: their hand + board + my hand and hidden board at the average.
        theirs = oh + board + (5 + hidden) * m
        return mine, theirs

    # ---------- the three calls ----------
    def move(self, obs):
        m = self.avg(obs)
        # Peek once, right after their first quote, if it told us nothing.
        if obs.round == 2:
            first = [px for r, who, px, q in obs.tape if who == "opp" and r == 1]
            if first and abs(first[0] - 15 * m) <= PEEK_TOL:
                return "PEEK"

        if any(who == "me" for _, who, _ in obs.discards):
            return None                   # the one swap is spent
        mine, theirs = self.fairs(obs)
        d = mine - theirs
        left = 5 - obs.round + 1          # trading rounds left, this one included
        # Expected final position: where I am, plus where my edge will push me.
        drift = 2 * left * max(-1.0, min(1.0, d / 4.0)) if abs(d) > 2 else 0.0
        final = max(-LIMIT, min(LIMIT, obs.position + drift))
        lo = min(range(5), key=lambda i: obs.hand[i])
        hi = max(range(5), key=lambda i: obs.hand[i])
        need = 1 if obs.round == 5 else 3     # be sure of the direction before round 5
        if final >= need and obs.hand[lo] <= m - SWAP_GAP:
            return ("SWAP", lo)
        if final <= -need and obs.hand[hi] >= m + SWAP_GAP:
            return ("SWAP", hi)
        return None

    def quote(self, obs):
        mine, theirs = self.fairs(obs)
        skew = max(-SKEW_MAX, min(SKEW_MAX, SKEW_K * (mine - theirs)))
        return theirs + skew + self.rng.uniform(-NOISE, NOISE)

    def respond(self, obs, price):
        edge = self.fairs(obs)[0] - price
        if edge > 3:
            return 2
        if edge > 2:
            return 1
        if edge < -3:
            return -2
        if edge < -2:
            return -1
        return 0
