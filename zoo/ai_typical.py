# Team Name: Zoo - ai_typical
# Members: Organisers
# Mentor: None

"""
ai_typical.py - strategies/sharp.py plus the three upgrades a typical
AI-written entry would make. Each is marked CHANGE 1/2/3 below.

  1. respond() also reads the price it is answering. sharp only reads the
     tape, where the quote being answered is not written yet.
  2. Expects the opponent's swap. If they have not swapped yet and a round is
     left, a long opponent will swap a low card up (stock rises), a short one
     a high card down (stock falls). fair() moves by OPP_SWAP_GAIN.
  3. quote() is shaded 30% of the way from fair toward the public estimate
     (board + unknown cards at the public average), so it gives less away.
"""

TRUST = 0.8
SWAP_EDGE = 3     # only swap a card this far from the average unseen rank
LOT_PER_TICK = 1  # one lot per tick of edge beyond the spread
# CHANGE 2: a sharp-style opponent with a fresh 5-card hand swaps its lowest
# card when it is 3 or less: P(1) x 6 + P(2) x 5 + P(3) x 4 = 3.9 points.
OPP_SWAP_GAIN = 3.9
SHADE = 0.3       # CHANGE 3: how far the quote moves from fair toward public


class Bot:
    def avg(self, obs):
        return sum((r + 1) * c for r, c in enumerate(obs.unseen)) / sum(obs.unseen)

    def public_estimate(self, obs):
        # CHANGE 3 (new): what anyone watching can work out. Only the board and
        # the discards are public, so start from a full deck and remove those.
        left = [4] * 13
        for r in obs.board:
            left[r - 1] -= 1
        for _, _, r in obs.discards:
            left[r - 1] -= 1
        public_avg = sum((r + 1) * c for r, c in enumerate(left)) / sum(left)
        return sum(obs.board) + (15 - len(obs.board)) * public_avg

    def fair(self, obs, latest=None):    # CHANGE 1: latest = the price being answered
        m = self.avg(obs)
        hidden_board = 5 - len(obs.board)
        opp_hand = sum(obs.opp_known) + (5 - len(obs.opp_known)) * m
        theirs = [px for r, who, px, q in obs.tape if who == "opp"]
        if latest is not None:
            theirs.append(latest)        # CHANGE 1: their freshest quote, not on the tape yet
        if theirs:
            implied = theirs[-1] - sum(obs.board) - (5 + hidden_board) * m
            opp_hand += TRUST * (implied - opp_hand)
        value = sum(obs.hand) + sum(obs.board) + opp_hand + hidden_board * m

        # CHANGE 2: their position is minus ours. Swaps happen at the start of
        # a round, so one is still to come only if they have not swapped and
        # this is not the last round.
        they_swapped = any(who == "opp" for _, who, _ in obs.discards)
        if not they_swapped and obs.round < 5:
            if obs.position < 0:         # they are long: they swap a low card up
                value += OPP_SWAP_GAIN
            elif obs.position > 0:       # they are short: they swap a high card down
                value -= OPP_SWAP_GAIN
        return value

    def move(self, obs):
        if any(who == "me" for _, who, _ in obs.discards):
            return None              # the one swap is spent
        m = self.avg(obs)
        lo = min(range(5), key=lambda i: obs.hand[i])
        hi = max(range(5), key=lambda i: obs.hand[i])
        if obs.position > 0 and obs.hand[lo] < m - SWAP_EDGE:
            return ("SWAP", lo)
        if obs.position < 0 and obs.hand[hi] > m + SWAP_EDGE:
            return ("SWAP", hi)
        return None

    def quote(self, obs):
        fair = self.fair(obs)
        return fair + SHADE * (self.public_estimate(obs) - fair)   # CHANGE 3: was fair

    def respond(self, obs, price):
        edge = self.fair(obs, price) - price                       # CHANGE 1: was self.fair(obs)
        lots = int((abs(edge) - 2) * LOT_PER_TICK) + 1 if abs(edge) > 2 else 0
        return min(2, lots) * (1 if edge > 0 else -1)
