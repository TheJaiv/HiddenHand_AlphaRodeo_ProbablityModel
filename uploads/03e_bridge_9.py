# Team Name: Alpha Rodeo
# Members: Jaiv Patel(26075057)
# Mentor: Arpit Gupta
# Upload note: bridge bot, pool about +9 (belief + identification + guarded quoting) (from zoo/bridge_9.py)

"""
bridge_9.py - a test opponent for the upper-middle strength band
(target: pool average +8.5..+10, weighted +7.5..+9 on the zoo pool).

BUILDING BLOCKS USED (all re-implemented here, nothing imported):
  * mid_bayes  - the CORE reader: a discrete belief over the opponent's hand
                 sum S (5..65), joint with how their quotes relate to S
                 (honest / noisy / hiding, plus a 'shaded' hypothesis added
                 here). Updated from their quotes (level-2: their reading of
                 MY quote is modelled, so my own echo is not taken for their
                 hand), from their buy / sell / pass on my quotes, and from
                 their swap.                                 [~+4.5 alone]
  * mid_exact  - exact identification of reader-family opponents: invert each
                 quote for every trust t on a grid and keep only whole,
                 consistent S. Extended here with a second profile, the
                 'typical AI' bot (quote shaded 30% to the public estimate,
                 fair value +-3.9 for the swap it expects from me, and it
                 reads the price it is answering). When one S survives, the
                 belief collapses onto it and I take 2 lots past the spread.
  * mid_steer  - CHECKED steering of identified readers: quote at the edge of
                 their no-trade band, on the side that moves their view of my
                 hand the way I want; their next quote is then mispriced and
                 I take it. Stops when they trade on a steering quote; the
                 identification itself checks they still act like a reader.
                 In round 5 (or once steering is off) the band edge is used
                 the other way: I quote just past it so they trade with me at
                 close to their own fair value.     [mid_exact+steer: ~+1.4]
  * mid_guard  - defensive quoting when not steering: quote what I think THEY
                 believe the stock is worth, skewed 50% (max 3) toward my
                 value, so my quotes say little about my hand.      [~+2.3]
  * old_plan   - quote noise of +-0.5 on guarded quotes.
  * new        - an opponent quote equal to the PUBLIC estimate (board + every
                 other card at the public average) is a hider's quote: it says
                 nothing about S and is skipped.
  The typical-AI profile in the identifier added ~+0.45 pool / +0.65 weighted.

Swap rule: sharp's (long -> throw a low card, short -> a high one). old_plan's
swap-on-expected-final-position was tried and did not help (switch left off).
Nothing is kept between deals: all state lives on self, and a fresh Bot() is
built for every deal.
"""

import math
import random

# ── belief (mid_bayes) ─────────────────────────────────────────────
LO, HI = 5, 65               # possible hand sums
NB = HI - LO + 1             # bins
DECK_SUM = 4 * 91            # sum of all 52 ranks
TRUST = 0.8                  # how far a reader-style opponent trusts my quote
# Hypotheses about how their quotes relate to S, carried jointly with S:
#   honest  quote = model fair + N(0, 2.5)
#   noisy   quote = model fair + N(0, 7)
#   hiding  quote = model fair at the PRIOR mean + N(0, 4): says nothing about S
#   shaded  quote = 70% model fair + 30% public estimate + N(0, 2.5)
SIGMAS = (2.5, 7.0, 4.0, 2.5)
HIDING = (False, False, True, False)
SHADES = (0.0, 0.0, 0.0, 0.3)
SIG_PRIOR = (0.45, 0.15, 0.25, 0.15)  # prior weight of each hypothesis
SIG_A = 0.8                  # softness of the buy/sell/pass thresholds
FLOOR = 0.01                 # floor on an answer likelihood
QFLOOR = 0.01                # floor on a quote likelihood
WIDE = 0.15                  # extra edge required per point of belief std-dev
HIDER_TOL = 0.02             # |quote - public estimate| below this = hider quote

# ── exact identification (mid_exact) ───────────────────────────────
T_GRID = [i / 10 for i in range(11)]   # trusts tested: 0.0 .. 1.0
TOL = 0.0051                           # quotes are rounded to 0.01
SHADE = 0.3          # 'typical' profile: quote = 70% fair + 30% public estimate
SHADE_G = 3.9        # ...and its fair adds the swap it still expects to make

# ── steering (mid_steer) ───────────────────────────────────────────
MARGIN = 1.9         # how far inside their +-2 band a steering quote sits
DECIDE_EDGE = 1.0    # |V - F| needed before committing to a direction
F_SPREAD = 0.3       # surviving trusts must agree on their fair this closely

# ── quoting / moves ────────────────────────────────────────────────
NOISE = 0.5          # uniform noise on ordinary quotes (old_plan)
SWAP_EDGE = 3        # sharp's swap threshold
GUARD = True         # mid_guard quoting when not steering
SKEW_K = 0.5
SKEW_MAX = 3.0
SWAP_FINAL = False   # old_plan swap on expected final position
SWAP_GAIN = 30.0
LOT_STEP = 1.0       # extra edge per extra lot when not identified (sharp: 1)
EXPLOIT = True       # late rounds vs an identified reader: quote so it trades at ~F
EXPLOIT_FROM = 5     # first round in which that replaces steering
SWAP_FROM = 3
LIMIT = 10           # position limit


def _phi(x):
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x * 0.7071067811865476))


def _public(board, discards, rnd):
    """Public estimate of the stock when a round-rnd quote was made: the
    board then + every other card at the average of the not-yet-public cards."""
    nb = rnd - 1
    B = sum(board[:nb])
    ds = [k for r, _, k in discards if r <= rnd]
    return B + (15 - nb) * (DECK_SUM - B - sum(ds)) / (52 - nb - len(ds))


class Bot:
    def __init__(self):
        # belief cache
        self._key = None
        self._mu = 0.0
        self._sd = 0.0
        # exact identification
        # (trust t, shade s) -> S at their last quote. s = 0: plain readers;
        # s = SHADE: the 'typical AI' profile (shaded quote, expects own swap).
        self.cand = {(t, s): None for t in T_GRID for s in (0.0, SHADE)}
        self.dead = False                       # not reader-family
        self.done = 0                           # opponent quotes processed
        self.last_round = 0
        self.S = None                           # identified S (at last quote)
        # steering
        self.dir = 0          # +1 steer them down (I buy), -1 steer up (I sell)
        self.off = False      # they traded on a steering quote: stop
        self.steered = []     # for each of my quotes: was it a steering quote?

    # ── pool helpers ────────────────────────────────────────────────
    @staticmethod
    def pool(obs):
        """(count, sum, mean, variance) of the ranks I have not seen."""
        n = sum(obs.unseen)
        tot = sum((r + 1) * c for r, c in enumerate(obs.unseen))
        sq = sum((r + 1) * (r + 1) * c for r, c in enumerate(obs.unseen))
        m = tot / n
        return n, tot, m, max(sq / n - m * m, 1e-6)

    # ── mid_exact: identification of reader-family opponents ───────
    @staticmethod
    def reader_quote(S, t, B, h, D, N, P):
        """What a trust-t reader with hand sum S quotes (= its fair value)."""
        U0 = DECK_SUM - B - D
        if P is None:
            c0, c1 = B, 5 + h
        else:
            c0, c1 = (1 - t) * B + t * P, 5 + h - t * (10 + h)
        return S + c0 + c1 * (U0 - S) / N

    def invert(self, F, t, B, h, D, N, P, tol):
        """The whole S that makes a trust-t reader have fair value F, or None."""
        U0 = DECK_SUM - B - D
        if P is None:
            c0, c1 = B, 5 + h
        else:
            c0, c1 = (1 - t) * B + t * P, 5 + h - t * (10 + h)
        a = 1 - c1 / N
        S = round((F - c0 - c1 * U0 / N) / a)
        if not LO <= S <= HI:
            return None
        pred = S + c0 + c1 * (U0 - S) / N
        return S if abs(pred - F) <= tol else None

    @staticmethod
    def swap_gain(rnd, my_pos, i_swapped, s):
        """The 'typical' profile (s > 0) adds the swap it still expects from ME
        (its opponent): +G when I am long (I would swap a low card up), -G when
        I am short. Only while I have not swapped and a round is left."""
        if s == 0 or i_swapped or rnd >= 5 or my_pos == 0:
            return 0.0
        return SHADE_G if my_pos > 0 else -SHADE_G

    def observe(self, F, rnd, board, discards, P, my_pos):
        """Filter (t, s) -> S candidates with one opponent quote F made in round rnd."""
        self.done += 1
        if self.dead:
            return
        pub = _public(board, discards, rnd)
        if abs(F - pub) < HIDER_TOL:
            self.dead, self.S = True, None      # a hider's quote: not reader-family
            return
        B, h = sum(board[:rnd - 1]), 5 - (rnd - 1)
        ds = [(r, w, k) for r, w, k in discards if r <= rnd]
        D, N = sum(k for _, _, k in ds), 47 - (rnd - 1) - len(ds)
        olds = [k for r, w, k in ds if w == "opp" and r > self.last_round]
        i_swapped = any(w == "me" for _, w, _ in ds)
        self.last_round = rnd
        new = {}
        for (t, sh), prev in self.cand.items():
            # undo the shading and the expected-swap term: their fair value
            fair = (F - sh * pub) / (1 - sh) - self.swap_gain(rnd, my_pos, i_swapped, sh)
            S = self.invert(fair, t, B, h, D, N, P, TOL / (1 - sh))
            if S is None:
                continue
            if prev is not None:
                if olds:
                    lo = prev - olds[0]
                    if not lo + 1 <= S <= lo + 13:
                        continue
                elif S != prev:
                    continue
            new[(t, sh)] = S
        self.cand = new
        sums = set(new.values())
        if not sums:
            self.dead, self.S = True, None
        else:
            self.S = sums.pop() if len(sums) == 1 else None

    def sync(self, obs, pending=None):
        """Feed every opponent quote not yet processed (and one being answered)."""
        quotes, P, pos = [], None, 0
        for r, who, px, q in obs.tape:
            if who == "me":
                P = px
                pos -= q
            else:
                quotes.append((px, r, P, pos))
                pos += q
        if pending is not None:
            quotes.append((pending, obs.round, P, obs.position))
        for px, r, p, mp in quotes[self.done:]:
            self.observe(px, r, obs.board, obs.discards, p, mp)

    def swapped_since(self, obs):
        """Cards the opponent discarded after their last processed quote."""
        return [k for r, w, k in obs.discards if w == "opp" and r > self.last_round]

    def exact_S(self, obs):
        """Identified S now (expected, if they swapped since their last quote)."""
        if self.S is None:
            return None
        S = self.S
        for k in self.swapped_since(obs):
            S += self.pool(obs)[2] - k
        return S

    def their_band(self, obs):
        """For an identified reader: (a, b, F) with its fair value when it answers
        my quote P being a + b*P (b = 0 for a reader of the tape only, b = t for
        the 'typical' profile, which also reads the price it is answering), and
        F its fair value right now. None if not pinned down."""
        if self.S is None or self.swapped_since(obs):
            return None
        P = None
        for r, who, px, q in obs.tape:
            if who == "me":
                P = px
        nb = len(obs.board)
        B = sum(obs.board)
        D = sum(k for _, _, k in obs.discards)
        N = 47 - nb - len(obs.discards)
        i_swapped = any(w == "me" for _, w, _ in obs.discards)
        out = []
        for (t, sh), S in self.cand.items():
            g = self.swap_gain(obs.round, obs.position, i_swapped, sh)
            if sh == 0:
                a = self.reader_quote(S, t, B, 5 - nb, D, N, P) + g
                out.append((a, 0.0, a))
            else:
                a = self.reader_quote(S, t, B, 5 - nb, D, N, 0.0) + g
                F = self.reader_quote(S, t, B, 5 - nb, D, N, P) + g
                out.append((a, t, F))
        if not out:
            return None
        if max(o[2] for o in out) - min(o[2] for o in out) > F_SPREAD:
            return None
        if len({o[1] for o in out}) > 1 or out[0][1] > 0.95:
            return None                      # trusts disagree, or no finite band
        n = len(out)
        return (sum(o[0] for o in out) / n, out[0][1], sum(o[2] for o in out) / n)

    # ── mid_bayes: the opponent model and belief ────────────────────
    @staticmethod
    def opp_fair(S, rnd, board, disc, my_px):
        """Fair value a reader-style opponent with hand sum S computes in round rnd,
        having seen my quote my_px (None if none). Reading my quote here is the
        level-2 step: the echo of my own quote is not mistaken for their hand."""
        nb = rnd - 1
        B = sum(board[:nb])
        N = 47 - nb - len(disc)
        m = (DECK_SUM - S - B - sum(disc)) / N
        mine = 5 * m
        if my_px is not None:
            implied = my_px - B - (10 - nb) * m
            mine += TRUST * (implied - mine)
        return S + B + mine + (5 - nb) * m

    def belief(self, obs, pending=None):
        """(mean, std) of the opponent hand sum S from the public record."""
        key = (len(obs.tape), len(obs.board), len(obs.discards), obs.round, pending)
        if key == self._key:
            return self._mu, self._sd
        n, tot, m, var = self.pool(obs)
        opp_sw = [(r, d) for r, who, d in obs.discards if who == "opp"]
        if opp_sw:
            k, base = 4, opp_sw[0][1]
        else:
            k, base = 5, 0
        pm = base + k * m
        pv = k * var * (n - k) / max(n - 1, 1)
        g = [math.exp(-0.5 * (s - pm) ** 2 / pv) for s in range(LO, HI + 1)]
        W = [[p * x for x in g] for p in SIG_PRIOR]
        card_p = [c / n for c in obs.unseen]

        pos = 0
        last_me = None
        tape = obs.tape
        if pending is not None:
            tape = tape + ((obs.round, "opp", pending, 0),)
        i = 0
        for rnd in range(1, obs.round + 1):
            disc = [d for r, _, d in obs.discards if r <= rnd]
            # their swap: S -> S - d + c, c drawn from the unseen pool
            for r, d in opp_sw:
                if r == rnd:
                    for kk, w in enumerate(W):
                        nw = [0.0] * NB
                        for j, p in enumerate(w):
                            if p < 1e-12:
                                continue
                            for c, q in enumerate(card_p):
                                if q:
                                    t = j - d + c + 1
                                    t = 0 if t < 0 else (NB - 1 if t >= NB else t)
                                    nw[t] += p * q
                        W[kk] = nw
            while i < len(tape) and tape[i][0] == rnd:
                _, who, px, qty = tape[i]
                i += 1
                f0 = self.opp_fair(LO, rnd, obs.board, disc, last_me)
                slope = self.opp_fair(LO + 1, rnd, obs.board, disc, last_me) - f0
                if who == "opp":
                    pos += qty
                    # hider filter: a quote at the public estimate says nothing
                    pub = _public(obs.board, obs.discards, rnd)
                    if abs(px - pub) < HIDER_TOL:
                        continue
                    for kk, sg in enumerate(SIGMAS):
                        w = W[kk]
                        if HIDING[kk]:
                            z = (px - f0 - slope * (pm - LO)) / sg
                            lk = math.exp(-0.5 * z * z) / sg + 1e-9
                            for j in range(NB):
                                w[j] *= lk
                            continue
                        sh = SHADES[kk]
                        a0 = (1 - sh) * f0 + sh * pub
                        a1 = (1 - sh) * slope
                        for j in range(NB):
                            z = (px - a0 - a1 * j) / sg
                            w[j] *= math.exp(-0.5 * z * z) / sg + QFLOOR
                else:
                    last_me = px
                    if not (qty == 0 and abs(pos) >= LIMIT):
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
            if z <= 0:
                W = [[1.0] * NB for _ in SIGMAS]
                z = float(NB * len(SIGMAS))
            W = [[x / z for x in w] for w in W]

        marg = [sum(w[j] for w in W) for j in range(NB)]
        mu = sum((LO + j) * p for j, p in enumerate(marg))
        sd = math.sqrt(max(sum((LO + j - mu) ** 2 * p for j, p in enumerate(marg)), 0.0))
        self._key, self._mu, self._sd = key, mu, sd
        return mu, sd

    def fair(self, obs, pending=None):
        """(my value of the stock, std of my S estimate). Identified opponent:
        exact S. Otherwise the Bayesian belief."""
        S = self.exact_S(obs)
        if S is not None:
            mu, sd = S, 0.0
        else:
            mu, sd = self.belief(obs, pending)
        n, tot, _, _ = self.pool(obs)
        hb = 5 - len(obs.board)
        rest = (tot - mu) / max(n - 5, 1)
        return sum(obs.hand) + sum(obs.board) + mu + hb * rest, sd

    # ── the three actions ───────────────────────────────────────────
    def move(self, obs):
        try:
            return self._move(obs)
        except Exception:
            return None

    def quote(self, obs):
        try:
            return self._quote(obs)
        except Exception:                    # never hand the house quote of 105 away
            m = self.pool(obs)[2]
            return sum(obs.hand) + sum(obs.board) + (10 - len(obs.board)) * m

    def respond(self, obs, price):
        try:
            return self._respond(obs, price)
        except Exception:
            return 0

    def _move(self, obs):
        """sharp's rule: long -> swap a low card away, short -> a high one."""
        self.sync(obs)
        if any(who == "me" for _, who, _ in obs.discards):
            return None
        m = self.pool(obs)[2]
        if SWAP_FINAL:
            if obs.round < SWAP_FROM:
                return None
            V, _ = self.fair(obs)
            opp_q = [px for r, who, px, q in obs.tape if who == "opp"]
            ref = opp_q[-1] if opp_q else _public(obs.board, obs.discards, obs.round)
            edge = V - ref
            step = 1 if edge > 0 else (-1 if edge < 0 else 0)
            final = max(-LIMIT, min(LIMIT, obs.position + (6 - obs.round) * 2 * step))
            best = max(range(5), key=lambda i: final * (m - obs.hand[i]))
            if final * (m - obs.hand[best]) > SWAP_GAIN:
                return ("SWAP", best)
            return None
        lo = min(range(5), key=lambda i: obs.hand[i])
        hi = max(range(5), key=lambda i: obs.hand[i])
        if obs.position > 0 and obs.hand[lo] < m - SWAP_EDGE:
            return ("SWAP", lo)
        if obs.position < 0 and obs.hand[hi] > m + SWAP_EDGE:
            return ("SWAP", hi)
        return None

    def _quote(self, obs):
        self.sync(obs)
        V, _ = self.fair(obs)
        # A trade on my last steering quote: they are no 2-wide reader. Stop.
        mine = [qty for r, who, px, qty in obs.tape if who == "me"]
        if mine and mine[-1] and self.steered and self.steered[-1]:
            self.off = True
        band = self.their_band(obs)
        if band is not None:
            a, b, F = band
            if obs.round < EXPLOIT_FROM and not self.off:
                if not self.dir and abs(V - F) > DECIDE_EDGE:
                    self.dir = 1 if V > F else -1          # chosen once per deal
                room = LIMIT - obs.position if self.dir > 0 else LIMIT + obs.position
                if self.dir and room > 0 and self.dir * (V - F) > 0:
                    # the lowest (dir +1) / highest (dir -1) price they still pass on
                    self.steered.append(True)
                    return (a - self.dir * MARGIN) / (1 - b)   # no noise: stay in the band
            if EXPLOIT and (obs.round >= EXPLOIT_FROM or self.off):
                # make them trade on my side at close to their own fair value
                d = 1 if V > F else -1
                best, best_p = 2.2, None
                for k, lots in ((3.01, 2), (2.05, 1)):
                    P = (a + d * k) / (1 - b)
                    gain = lots * (d * (V - P) + 2)
                    if gain > best:
                        best, best_p = gain, P
                if best_p is not None:
                    self.steered.append(False)
                    return best_p
        self.steered.append(False)
        if GUARD:
            mu = self.exact_S(obs)
            if mu is None:
                mu = self.belief(obs)[0]
            m = self.pool(obs)[2]
            theirs = mu + sum(obs.board) + (10 - len(obs.board)) * m
            skew = max(-SKEW_MAX, min(SKEW_MAX, SKEW_K * (V - theirs)))
            return theirs + skew + random.uniform(-NOISE, NOISE)
        return V + random.uniform(-NOISE, NOISE)

    def _respond(self, obs, price):
        self.sync(obs, pending=price)
        V, sd = self.fair(obs, price)
        edge = V - price
        if self.S is not None:                     # identified: full size past the spread
            return 2 if edge > 2 else (-2 if edge < -2 else 0)
        need = 2.0 + WIDE * sd
        if abs(edge) <= need:
            return 0
        lots = int((abs(edge) - need) / LOT_STEP) + 1
        return min(2, lots) * (1 if edge > 0 else -1)
