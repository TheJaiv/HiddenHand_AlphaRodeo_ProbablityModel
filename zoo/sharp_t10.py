# Team Name: Zoo - sharp_t10
# Members: Organisers
# Mentor: None

"""
sharp_t10.py - strategies/sharp.py with TRUST = 1.0.

  * The ONLY change: it takes the opponent's last quote at face value and
    reads their hand straight off it, ignoring the card-counting prior.
"""

TRUST = 1.0       # CHANGE: was 0.8. Believe the opponent's last quote completely
SWAP_EDGE = 3     # only swap a card this far from the average unseen rank
LOT_PER_TICK = 1  # one lot per tick of edge beyond the spread


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
        return self.fair(obs)

    def respond(self, obs, price):
        edge = self.fair(obs) - price
        lots = int((abs(edge) - 2) * LOT_PER_TICK) + 1 if abs(edge) > 2 else 0
        return min(2, lots) * (1 if edge > 0 else -1)
