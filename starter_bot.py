# Team Name: Alpha Rodeo
# Members: Jaiv Patel(26075057)
# Mentor: Arpit Gupta

"""
starter_bot.py - Hidden Hand: copy this file, rename it, make it yours.

A fresh Bot() is built for every deal, so anything you store on self lasts
exactly one deal. Three methods, each called with an Obs (see rules.py):

    move(obs)            once per round, before trading:
                           None          do nothing
                           "PEEK"        pay 3, see one random card of their hand
                           ("SWAP", i)   discard obs.hand[i] face up, draw a new card
                                         (once per deal)
    quote(obs)           you are the maker: name a price. They may buy from
                         you at price + 2 or sell to you at price - 2.
    respond(obs, price)  they quoted price: return how many lots to trade,
                         +n to buy n at price + 2, -n to sell n at price - 2,
                         0 to pass. At most 2 lots, and your position stays
                         within +-10.

The stock settles at the sum of all 15 cards: your hand, their hand and the
whole board (A=1 ... K=13). As written, this bot IS the house's `naive` bot:
it scores exactly 0 against it, so there is everything left to win.
"""


TRUST = 0.8 # how much u beileve the opponent is telling the truth 
SWAP_EDGE = 3     # only swap a card this far from the average unseen rank
LOT_PER_TICK = 1  # one lot per tick of edge beyond the spread


class Bot:
    def avg(self, obs):  # the average rank of a card you haven't seen.
        return sum((r + 1) * c for r, c in enumerate(obs.unseen)) / sum(obs.unseen)    # enumerate(obs.unseen) yields (0, 4), (1, 3), (2, 4), (3, 4), .... Index r runs from 0, so r + 1 is the rank.

    def fair(self, obs):  # ur estimated stock
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
