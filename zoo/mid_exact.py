# Team Name: Zoo - mid_exact
# Members: AI
# Mentor: None

"""
mid_exact.py - sharp, plus exact identification of reader-family opponents.

A reader-family bot (naive, reader, sharp, any trust t) quotes its fair value
    F = S + B + O + h*m
S = its hand sum, B = board shown, h = hidden board cards, m = its average
unseen rank, O = its estimate of our hand: 5m moved a fraction t towards what
our last quote P implies (P - B - (5+h)m). Its m is public except for S:
    m = (364 - S - B - D) / N,   D = sum of all discards, N = 47 - |board| - |discards|
so F is linear in S. Quotes are rounded to 0.01 and S is whole, so for each t
on a grid we invert the quote and keep (t, S) only if S comes out whole and is
consistent with the previous quote (S unchanged, or moved by -old+1..-old+13
after a visible opponent swap of card `old`). One surviving S = identified.

Identified: value the stock with the exact S, trade 2 lots past the spread.
Otherwise: sharp's reading (trust 0.8). Quoting and swapping are sharp's.
"""

TRUST = 0.8                                  # sharp's fallback trust
SWAP_EDGE = 3                                # sharp's swap threshold
LOT_PER_TICK = 1                             # sharp's sizing
T_GRID = [i / 10 for i in range(11)]         # trusts we test for: 0.0 .. 1.0
TOL = 0.0051                                 # quotes are rounded to 0.01
DECK_SUM = 4 * 91                            # sum of all 52 ranks


class Bot:
    def __init__(self):
        self.cand = {t: None for t in T_GRID}  # t -> S at last quote (None = any)
        self.dead = False                      # no (t, S) fits: not reader-family
        self.done = 0                          # opponent quotes already processed
        self.last_round = 0                    # round of the last processed quote
        self.S = None                          # identified hand sum (at last quote)

    # ── identification ──────────────────────────────────────────
    def invert(self, F, t, B, h, D, N, P):
        """The whole S that makes a trust-t reader quote F, or None."""
        U0 = DECK_SUM - B - D                  # unseen sum to them, plus their S
        if P is None:                          # no quote of ours yet: t plays no part
            c0, c1 = B, 5 + h
        else:
            c0, c1 = (1 - t) * B + t * P, 5 + h - t * (10 + h)
        a = 1 - c1 / N                         # F = a*S + c0 + c1*U0/N
        S = round((F - c0 - c1 * U0 / N) / a)
        if not 5 <= S <= 65:
            return None
        pred = S + c0 + c1 * (U0 - S) / N
        return S if abs(pred - F) <= TOL else None

    def observe(self, F, rnd, board, discards, P):
        """Filter the (t, S) candidates with one opponent quote F made in round rnd."""
        self.done += 1
        if self.dead:
            return
        B, h = sum(board[:rnd - 1]), 5 - (rnd - 1)
        ds = [(r, w, k) for r, w, k in discards if r <= rnd]
        D, N = sum(k for _, _, k in ds), 47 - (rnd - 1) - len(ds)
        # their swaps since the last processed quote (at most one per deal)
        olds = [k for r, w, k in ds if w == "opp" and r > self.last_round]
        self.last_round = rnd
        new = {}
        for t, prev in self.cand.items():
            S = self.invert(F, t, B, h, D, N, P)
            if S is None:
                continue
            if prev is not None:
                if olds:
                    lo = prev - olds[0]
                    if not lo + 1 <= S <= lo + 13:
                        continue
                elif S != prev:
                    continue
            new[t] = S
        self.cand = new
        sums = set(new.values())
        if not sums:
            self.dead, self.S = True, None
        else:
            self.S = sums.pop() if len(sums) == 1 else None

    def sync(self, obs, pending=None):
        """Process every opponent quote not yet seen (plus one being responded to)."""
        quotes, P = [], None
        for r, who, px, q in obs.tape:
            if who == "me":
                P = px
            else:
                quotes.append((px, r, P))
        if pending is not None:
            quotes.append((pending, obs.round, P))
        for px, r, p in quotes[self.done:]:
            self.observe(px, r, obs.board, obs.discards, p)

    def exact_S(self, obs):
        """The opponent's current hand sum if identified (expected, if they just swapped)."""
        if self.S is None:
            return None
        S = self.S
        for r, w, k in obs.discards:            # swapped since their last quote
            if w == "opp" and r > self.last_round:
                S += self.avg(obs) - k
        return S

    # ── valuation (sharp, unless identified) ───────────────────
    def avg(self, obs):
        return sum((r + 1) * c for r, c in enumerate(obs.unseen)) / sum(obs.unseen)

    def fair(self, obs):
        hidden_board = 5 - len(obs.board)
        S = self.exact_S(obs)
        if S is not None:
            # Opponent hand known: hidden board cards average the rest of the unseen.
            U = sum((r + 1) * c for r, c in enumerate(obs.unseen))
            n = sum(obs.unseen)
            rest = (U - S) / (n - 5)
            return sum(obs.hand) + sum(obs.board) + S + hidden_board * rest
        m = self.avg(obs)
        opp_hand = sum(obs.opp_known) + (5 - len(obs.opp_known)) * m
        theirs = [px for r, who, px, q in obs.tape if who == "opp"]
        if theirs:
            implied = theirs[-1] - sum(obs.board) - (5 + hidden_board) * m
            opp_hand += TRUST * (implied - opp_hand)
        return sum(obs.hand) + sum(obs.board) + opp_hand + hidden_board * m

    # ── the three calls ─────────────────────────────────────────
    def move(self, obs):
        self.sync(obs)
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
        self.sync(obs)
        return self.fair(obs)

    def respond(self, obs, price):
        self.sync(obs, pending=price)
        edge = self.fair(obs) - price
        if self.S is not None:                   # identified: full size past the spread
            return 2 if edge > 2 else (-2 if edge < -2 else 0)
        lots = int((abs(edge) - 2) * LOT_PER_TICK) + 1 if abs(edge) > 2 else 0
        return min(2, lots) * (1 if edge > 0 else -1)
