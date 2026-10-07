# Team Name: Zoo - hider
# Members: Organisers
# Mentor: None

"""
hider.py - strategies/sharp.py that never shows its hand in its quotes.

  * quote() is the PUBLIC estimate: the board plus 15 - len(board) cards at
    the average of every card not yet public (board and discards only). Its
    own hand counts as unknown, so the quote says nothing about it.
  * respond() and move() are sharp's: it still trades on its real fair value.
"""

TRUST = 0.8
SWAP_EDGE = 3     # only swap a card this far from the average unseen rank
LOT_PER_TICK = 1  # one lot per tick of edge beyond the spread


class Bot:
    def avg(self, obs):
        return sum((r + 1) * c for r, c in enumerate(obs.unseen)) / sum(obs.unseen)

    def public_estimate(self, obs):
        # CHANGE (new): what anyone watching can work out. Only the board and
        # the discards are public, so start from a full deck and remove those.
        left = [4] * 13
        for r in obs.board:
            left[r - 1] -= 1
        for _, _, r in obs.discards:
            left[r - 1] -= 1
        public_avg = sum((r + 1) * c for r, c in enumerate(left)) / sum(left)
        return sum(obs.board) + (15 - len(obs.board)) * public_avg

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
        return self.public_estimate(obs)   # CHANGE: was self.fair(obs)

    def respond(self, obs, price):
        edge = self.fair(obs) - price
        lots = int((abs(edge) - 2) * LOT_PER_TICK) + 1 if abs(edge) > 2 else 0
        return min(2, lots) * (1 if edge > 0 else -1)
