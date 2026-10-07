# Team Name: Zoo - liar
# Members: Organisers
# Mentor: None

"""
liar.py - strategies/sharp.py that bluffs in rounds 1 and 2.

  * Rounds 1-2: quotes fair - 2 x (own hand - 5 x avg). A hand 6 points above
    average is quoted 12 below fair, so a reader thinks the hand is 6 points
    BELOW average: the quote shows the mirror image of the real hand.
  * Round 3 on: quotes fair, like sharp. respond() and move() are sharp's.
"""

TRUST = 0.8
SWAP_EDGE = 3     # only swap a card this far from the average unseen rank
LOT_PER_TICK = 1  # one lot per tick of edge beyond the spread
LIE_ROUNDS = 2    # CHANGE (new): bluff in rounds 1..LIE_ROUNDS, honest after


class Bot:
    def avg(self, obs):
        return sum((r + 1) * c for r, c in enumerate(obs.unseen)) / sum(obs.unseen)

    def fair(self, obs):
        m = self.avg(obs)
        hidden_board = 5 - len(obs.board)
        opp_hand = sum(obs.opp_known) + (5 - len(obs.opp_known)) * m
        theirs = [px for r, who, px, q in obs.tape if who == "opp"]
        if theirs:
            implied = theirs[-1] - sum(obs.board) - (5 + hidden_board) * m
            opp_hand += TRUST * (implied - opp_hand)
        return sum(obs.hand) + sum(obs.board) + opp_hand + hidden_board * m

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
        # CHANGE: was just self.fair(obs). Early on, flip the hand's signal.
        if obs.round <= LIE_ROUNDS:
            excess = sum(obs.hand) - 5 * self.avg(obs)   # + strong hand, - weak hand
            return self.fair(obs) - 2 * excess
        return self.fair(obs)

    def respond(self, obs, price):
        edge = self.fair(obs) - price
        lots = int((abs(edge) - 2) * LOT_PER_TICK) + 1 if abs(edge) > 2 else 0
        return min(2, lots) * (1 if edge > 0 else -1)
