# Team Name: Alpha Rodeo
# Members: Jaiv Patel(26075057)
# Mentor: Arpit Gupta
# Upload note: mid bot with a probability belief over the opponent's hand (from zoo/mid_bayes.py)

"""
mid_bayes.py - sharp, plus a probabilistic belief about the opponent's hand sum S.

The belief is a discrete distribution over S = 5..65. It is rebuilt from the
public record on every call (cheap: ~10 events x 61 bins):

  prior   5 cards drawn from the pool I cannot see (normal approximation with
          the finite-population correction). If the opponent swapped, their
          ORIGINAL hand is known to contain the discarded card.
  quotes  each opponent quote is taken to be a reader-style fair value
          (their hand + board + their reading of my last quote + hidden board x
          their average unseen rank) plus Gaussian noise of a few points. The
          noise level is itself uncertain: honest / noisy / hiding hypotheses
          are carried jointly with S (see SIGMAS).
  answers each opponent answer to MY quote P: bought -> their fair > P + 2,
          sold -> fair < P - 2, passed -> within +-2 (soft, probit edges).
          A pass forced by the +-10 position limit is ignored.
          When I am the taker, the quote I am answering is used too.
  swap    the opponent's swap moves S by (new card - discarded card); the new
          card's rank is drawn from the unseen pool, which widens the belief.

Every likelihood has a small floor so one odd quote cannot zero the belief.
Value = my cards + board + E[S] + hidden board x average of what is left.
Trading uses sharp's sizing, with extra required edge when the belief is wide.
Quote = that honest fair value. Swap rule = sharp's.
"""

import math

LO, HI = 5, 65               # possible hand sums
NB = HI - LO + 1             # bins
DECK_SUM = 4 * 91            # sum of all 52 ranks
TRUST = 0.8                  # how far a reader-style opponent trusts my quote
# How their quotes relate to S: three hypotheses k, carried jointly with S.
#   honest (quote = model fair + N(0, 2.5)), noisy (+ N(0, 7)), and
#   hiding (quote = model fair at the PRIOR mean + N(0, 4): says nothing about S).
SIGMAS = (2.5, 7.0, 4.0)
HIDING = (False, False, True)
SIG_PRIOR = (0.5, 0.2, 0.3)  # prior weight of each hypothesis
SIG_A = 0.8                  # softness of the buy/sell/pass thresholds
FLOOR = 0.01                 # floor on an answer likelihood (robustness)
QFLOOR = 0.01                # floor on a quote likelihood: any one quote may be a lie
WIDE = 0.15                  # extra edge required per point of belief std-dev
SWAP_EDGE = 3                # sharp's swap threshold
LIMIT = 10                   # position limit


def _phi(x):
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x * 0.7071067811865476))


class Bot:
    def __init__(self):
        self._key = None     # cache: belief is only rebuilt when the record changes
        self._mu = 0.0
        self._sd = 0.0

    # ── pool helpers ────────────────────────────────────────
    @staticmethod
    def pool(obs):
        """(count, sum, mean, variance) of the ranks I have not seen."""
        n = sum(obs.unseen)
        tot = sum((r + 1) * c for r, c in enumerate(obs.unseen))
        sq = sum((r + 1) * (r + 1) * c for r, c in enumerate(obs.unseen))
        m = tot / n
        return n, tot, m, max(sq / n - m * m, 1e-6)

    # ── the opponent model: their reader-style fair value given S ──
    @staticmethod
    def opp_fair(S, rnd, board, disc, my_px):
        """Fair value a reader-style opponent with hand sum S would compute in
        round `rnd`. board/disc: what was face up then. my_px: my latest quote
        they had seen (None if none)."""
        nb = rnd - 1
        B = sum(board[:nb])
        N = 47 - nb - len(disc)                 # cards they cannot see
        m = (DECK_SUM - S - B - sum(disc)) / N  # their average unseen rank
        mine = 5 * m                            # their estimate of my hand
        if my_px is not None:
            implied = my_px - B - (10 - nb) * m
            mine += TRUST * (implied - mine)
        return S + B + mine + (5 - nb) * m

    # ── the belief ──────────────────────────────────────────
    def belief(self, obs, pending=None):
        """Return (mean, std) of the opponent hand sum S, rebuilding if needed.
        pending: an opponent quote I am answering right now (not yet on the tape).

        The belief is joint over (S, k): k says how their quotes relate to S
        (honest / noisy / hiding). An honest quoter keeps the weight on the
        tight hypothesis; for a bot whose quotes sit at the uninformed price
        (or whose trades contradict its quotes) weight moves to hiding/noisy,
        and its quotes then move S less and the belief stays wide."""
        key = (len(obs.tape), len(obs.board), len(obs.discards), obs.round, pending)
        if key == self._key:
            return self._mu, self._sd
        n, tot, m, var = self.pool(obs)
        opp_sw = [(r, d) for r, who, d in obs.discards if who == "opp"]
        # Prior on the opponent's ORIGINAL hand.
        if opp_sw:
            k, base = 4, opp_sw[0][1]           # they held the discarded card
        else:
            k, base = 5, 0
        pm = base + k * m
        pv = k * var * (n - k) / max(n - 1, 1)
        g = [math.exp(-0.5 * (s - pm) ** 2 / pv) for s in range(LO, HI + 1)]
        W = [[p * x for x in g] for p in SIG_PRIOR]  # W[k][j]: noise k, S = LO + j
        card_p = [c / n for c in obs.unseen]        # rank of a freshly drawn card

        pos = 0                                  # my position as the tape is replayed
        last_me = None                           # my latest quote
        tape = obs.tape
        if pending is not None:
            tape = tape + ((obs.round, "opp", pending, 0),)
        i = 0
        for rnd in range(1, obs.round + 1):
            disc = [d for r, _, d in obs.discards if r <= rnd]
            # 1) an opponent swap happens before this round's quotes:
            #    S -> S - d + c, c drawn from the unseen pool (shift + widen)
            for r, d in opp_sw:
                if r == rnd:
                    for kk, w in enumerate(W):
                        nw = [0.0] * NB
                        for j, p in enumerate(w):
                            if p < 1e-15:
                                continue
                            for c, q in enumerate(card_p):
                                if q:
                                    t = j - d + c + 1
                                    t = 0 if t < 0 else (NB - 1 if t >= NB else t)
                                    nw[t] += p * q
                        W[kk] = nw
            # 2) the quotes of this round, in order. Their fair is linear in S:
            #    f(S) = f0 + slope * (S - LO), so get it from two points.
            while i < len(tape) and tape[i][0] == rnd:
                _, who, px, qty = tape[i]
                i += 1
                seen = last_me                   # my quote they had on the tape (reader-style)
                f0 = self.opp_fair(LO, rnd, obs.board, disc, seen)
                slope = self.opp_fair(LO + 1, rnd, obs.board, disc, seen) - f0
                if who == "opp":
                    # their quote ~ N(their fair, sigma_k); I was the taker
                    for kk, sg in enumerate(SIGMAS):
                        w = W[kk]
                        if HIDING[kk]:           # same likelihood for every S
                            z = (px - f0 - slope * (pm - LO)) / sg
                            lk = math.exp(-0.5 * z * z) / sg + 1e-9
                            for j in range(NB):
                                w[j] *= lk
                            continue
                        for j in range(NB):
                            z = (px - f0 - slope * j) / sg
                            w[j] *= math.exp(-0.5 * z * z) / sg + QFLOOR
                    pos += qty
                else:
                    last_me = px
                    if not (qty == 0 and abs(pos) >= LIMIT):   # skip forced passes
                        lik = []
                        for j in range(NB):
                            f = f0 + slope * j
                            if qty > 0:
                                q = _phi((f - px - 2) / SIG_A)
                            elif qty < 0:
                                q = _phi((px - 2 - f) / SIG_A)
                            else:
                                q = _phi((px + 2 - f) / SIG_A) - _phi((px - 2 - f) / SIG_A)
                            lik.append(FLOOR + q)
                        for w in W:
                            for j in range(NB):
                                w[j] *= lik[j]
                    pos -= qty
            z = sum(sum(w) for w in W)
            if z <= 0:                           # cannot happen with the floors; be safe
                W = [[1.0] * NB for _ in SIGMAS]
                z = float(NB * len(SIGMAS))
            W = [[x / z for x in w] for w in W]

        marg = [sum(w[j] for w in W) for j in range(NB)]  # marginal over S
        mu = sum((LO + j) * p for j, p in enumerate(marg))
        sd = math.sqrt(max(sum((LO + j - mu) ** 2 * p for j, p in enumerate(marg)), 0.0))
        self._key, self._mu, self._sd = key, mu, sd
        return mu, sd

    def fair(self, obs, pending=None):
        """My cards + board + E[S] + hidden board x average of the rest of the pool."""
        mu, _ = self.belief(obs, pending)
        n, tot, _, _ = self.pool(obs)
        hb = 5 - len(obs.board)
        rest = (tot - mu) / max(n - 5, 1)        # pool average once S is taken out
        return sum(obs.hand) + sum(obs.board) + mu + hb * rest

    # ── the three actions ───────────────────────────────────
    def move(self, obs):
        """sharp's rule: long -> swap a low card away, short -> a high one."""
        if any(who == "me" for _, who, _ in obs.discards):
            return None
        m = self.pool(obs)[2]
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
        """sharp's sizing (1 lot per tick of edge past the bar), with the bar
        raised a little while the belief about S is still wide."""
        _, sd = self.belief(obs, price)       # their quote is evidence too
        edge = self.fair(obs, price) - price
        need = 2.0 + WIDE * sd
        if abs(edge) <= need:
            return 0
        lots = int(abs(edge) - need) + 1
        return min(2, lots) * (1 if edge > 0 else -1)
