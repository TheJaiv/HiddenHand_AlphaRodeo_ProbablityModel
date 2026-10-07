# Team Name: Zoo - swapper
# Members: Organisers
# Mentor: None

"""
swapper.py - strategies/sharp.py that always swaps in round 2.

  * Round 2: swaps its most extreme card (the one furthest from the average
    unseen rank), long, short or flat. Never swaps in any other round.
  * quote() and respond() are sharp's.
"""

TRUST = 0.8
SWAP_EDGE = 3     # (unused now: swapper swaps whatever the gap)
LOT_PER_TICK = 1  # one lot per tick of edge beyond the spread
SWAP_ROUND = 2    # CHANGE (new): the round it always swaps in


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
        # CHANGE: was "swap the lowest if long, the highest if short, only past
        # SWAP_EDGE". Now: in SWAP_ROUND, swap the card furthest from average.
        if obs.round != SWAP_ROUND:
            return None
        m = self.avg(obs)
        extreme = max(range(5), key=lambda i: abs(obs.hand[i] - m))
        return ("SWAP", extreme)

    def quote(self, obs):
        return self.fair(obs)

    def respond(self, obs, price):
        edge = self.fair(obs) - price
        lots = int((abs(edge) - 2) * LOT_PER_TICK) + 1 if abs(edge) > 2 else 0
        return min(2, lots) * (1 if edge > 0 else -1)
