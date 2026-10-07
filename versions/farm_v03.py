# Team Name: Alpha Rodeo
# Members: Jaiv Patel(26075057)
# Mentor: Arpit Gupta
# Version: farm_v03, parent farm_v02, idea: vs a detected hider (exact public-estimate quote after round 1, no other quote) quote around what it believes, skewed toward my value

"""
bridge_11.py - a test opponent aimed between the mid bots and the rivals.

Building blocks it combines (all re-implemented here, nothing imported):
  * zoo/mid_bayes.py  - a discrete belief over the opponent's hand sum S
                        (honest / noisy / hiding mixture); quotes that equal
                        the public estimate (a hider) are ignored outright.
  * zoo/mid_exact.py  - exact whole-number identification of reader-family
                        opponents (any trust t on a 0.0..1.0 grid). When it
                        identifies S the belief collapses to that exact S.
                        Unlike mid_exact, a failed identification restarts
                        from the next quote (a liar becomes readable later).
  * zoo/mid_steer.py  - CHECKED steering: quote just inside an identified
                        reader's no-trade band to move its belief; if it
                        trades where the model says it will not, stop.
  * zoo/old_plan.py   - quote noise +-0.5, inventory skew, swap on the
                        expected final position, expected opponent swap.

Attacking layer (only against an identified reader, exact S and trust t):
  HARVEST  quote 3.02 outside its band on the side that profits us, so it
           takes 2 lots at a price we know is wrong.
  PLAN     a small look-ahead: for every quote of ours it tries honest,
           steer up/down, harvest buy/sell (and the limit trick below),
           simulates the reader's remaining quotes and answers, fills the
           10-lot limit greedily, and plays the best first quote.
  LIMIT    at +10 lots quote 195, at -10 quote 0: the opponent cannot trade
           in the harmful direction, but a reader believes the quote.

farm_v02: the identifier also tests the 'typical AI' profile (zoo/ai_typical.py):
  quote = 70% fair + 30% public estimate, fair +-3.9 for the swap it expects
  from me while I hold a position, and it answers with the fair of the price
  it is answering (band in my-price space is +-2/(1-t), e.g. +-10 at t=0.8).
  The planner steers / harvests that profile with its own band formula.
farm_v03: GUARD against a detected hider (it quoted exactly the public estimate
  after round 1 and never anything else): my quote is what it believes
  (my S estimate + board + the rest at the average) plus half my edge, max 3,
  so my quote no longer tells its trust-0.8 reading what my hand is.
"""

import math
import random

# ── belief (mid_bayes) ────────────────────────────────────────────────
LO, HI = 5, 65               # possible hand sums
NB = HI - LO + 1
DECK_SUM = 4 * 91            # sum of all 52 ranks
TRUST = 0.8                  # how far a reader-style opponent trusts my quote
SIGMAS = (2.5, 7.0, 4.0)     # honest / noisy / hiding quote noise
HIDING = (False, False, True)
SIG_PRIOR = (0.5, 0.2, 0.3)
SIG_A = 0.8                  # softness of the buy/sell/pass thresholds
FLOOR = 0.01
QFLOOR = 0.01
WIDE = 0.15                  # extra edge required per point of belief sd
PUB_TOL = 0.02               # a quote this close to the public estimate says nothing

# ── identification (mid_exact) ────────────────────────────────────────
T_GRID = [i / 10 for i in range(11)]
TOL = 0.0051                 # quotes are rounded to 0.01
SHADE = 0.3                  # 'typical AI' profile: quote = 70% fair + 30% public estimate
SHADE_G = 3.9                # ...and its fair adds the swap it expects from me
PROFILES = [(t, 0.0) for t in T_GRID] + [(t, SHADE) for t in T_GRID]

# ── quoting / moves (old_plan) ────────────────────────────────────────
NOISE = 0.5
SKEW = 0.2
SWAP_GAIN = 30.0
SWAP_FROM = 3
OPP_SWAP_K = 0.5
LIMIT = 10
GUARD = True                 # unidentified opponent: quote near what they believe
GSKEW_K = 0.5                # ...skewed this much toward my value
GSKEW_MAX = 3.0              # ...by at most this

# ── attack layer ──────────────────────────────────────────────────────
STEER_IN = 1.98              # inside their +-2 band: no trade, belief moves
HARVEST_OUT = 3.02           # outside it: sharp sizing gives 2 lots at edge >= 3
RESP_MARGIN = 0.2            # extra edge I want when answering an identified reader
DEPTH = 4                    # quotes of mine explored with every option
USE_LIMIT_TRICK = True
USE_HARVEST = True
USE_STEER = True


def _phi(x):
    return 0.5 * (1.0 + math.erf(x * 0.7071067811865476))


def _lots(e):
    """sharp's sizing for a taker with edge e: signed lots (+ buy)."""
    a = abs(e)
    if a <= 2:
        return 0
    n = min(2, int(a - 2) + 1)
    return n if e > 0 else -n


class Bot:
    def __init__(self):
        # identification state
        self.cand = {k: None for k in PROFILES}   # (t, shade) -> S (None = any)
        self.nq = 0              # consistent quotes since the last reset
        self.pnone = False       # first quote since reset came before any quote of mine
        self.done = 0            # opponent quotes processed
        self.last_round = 0      # round of the last processed quote
        self.peeked = False      # they peeked: their fair has terms I cannot see
        self.npub = 0            # their quotes at the public estimate
        self.nreal = 0           # their quotes anywhere else
        # attack state
        self.off = False         # an identified reader did not answer as modelled
        self.check = None        # (tape index, expected sign of their qty)
        # belief cache
        self._key = None
        self._mu = 0.0
        self._sd = 0.0

    # ── pool helpers ──────────────────────────────────────────────────
    @staticmethod
    def pool(obs):
        n = sum(obs.unseen)
        tot = sum((r + 1) * c for r, c in enumerate(obs.unseen))
        sq = sum((r + 1) * (r + 1) * c for r, c in enumerate(obs.unseen))
        m = tot / n
        return n, tot, m, max(sq / n - m * m, 1e-6)

    @staticmethod
    def public_at(board, discards, rnd):
        """The public estimate a hider quotes in round rnd."""
        nb = rnd - 1
        B = sum(board[:nb])
        ds = [k for r, _, k in discards if r <= rnd]
        return B + (15 - nb) * (DECK_SUM - B - sum(ds)) / (52 - nb - len(ds))

    # ══ identification (mid_exact, with restart) ══════════════════════
    @staticmethod
    def invert(F, t, B, h, D, N, P, tol=TOL):
        U0 = DECK_SUM - B - D
        if P is None:
            c0, c1 = B, 5 + h
        else:
            c0, c1 = (1 - t) * B + t * P, 5 + h - t * (10 + h)
        a = 1 - c1 / N
        S = round((F - c0 - c1 * U0 / N) / a)
        if not 5 <= S <= 65:
            return None
        pred = S + c0 + c1 * (U0 - S) / N
        return S if abs(pred - F) <= tol else None

    @staticmethod
    def gain(sh, rnd, my_pos, i_swapped):
        """The typical profile adds the swap it still expects from me."""
        if sh == 0 or i_swapped or rnd >= 5 or my_pos == 0:
            return 0.0
        return SHADE_G if my_pos > 0 else -SHADE_G

    def inv(self, F, key, B, h, D, N, P, pub, g):
        t, sh = key
        if sh == 0:
            return self.invert(F, t, B, h, D, N, P)
        fair = (F - sh * pub) / (1 - sh) - g
        return self.invert(fair, t, B, h, D, N, P, TOL / (1 - sh))

    def observe(self, F, rnd, obs, P, my_pos=0):
        self.done += 1
        if self.peeked:
            return
        pub = self.public_at(obs.board, obs.discards, rnd)
        if abs(F - pub) < PUB_TOL:
            if abs(F - pub) < 0.0055 and rnd > 1:   # exactly the public estimate
                # (round 1 does not count: an average hand quotes 105 too)
                self.npub += 1
            return                                  # a hider's quote: no information
        self.nreal += 1
        B, h = sum(obs.board[:rnd - 1]), 5 - (rnd - 1)
        ds = [(r, w, k) for r, w, k in obs.discards if r <= rnd]
        D, N = sum(k for _, _, k in ds), 47 - (rnd - 1) - len(ds)
        olds = [k for r, w, k in ds if w == "opp" and r > self.last_round]
        i_sw = any(w == "me" for _, w, _ in ds)
        self.last_round = rnd
        new = {}
        for t, prev in self.cand.items():
            S = self.inv(F, t, B, h, D, N, P, pub, self.gain(t[1], rnd, my_pos, i_sw))
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
        if new:
            self.cand = new
            self.nq += 1
            return
        # nothing fits: restart, this quote is the first of a new run
        self.cand, self.nq = {}, 0
        for t in PROFILES:
            S = self.inv(F, t, B, h, D, N, P, pub, self.gain(t[1], rnd, my_pos, i_sw))
            if S is not None:
                self.cand[t] = S
        if self.cand:
            self.nq, self.pnone = 1, P is None
        else:
            self.cand = {t: None for t in PROFILES}

    def sync(self, obs, pending=None):
        if any(w == "opp" for _, w in obs.peeks):
            self.peeked = True
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
            if self.nq == 0:
                self.pnone = p is None
            self.observe(px, r, obs, p, mp)

    def ident(self):
        """(S, sorted (trust, shade) keys) of an identified reader, or None."""
        if self.peeked or not self.cand or self.nq == 0:
            return None
        sums = set(self.cand.values())
        if len(sums) != 1 or None in sums:
            return None
        if self.nq < 2 and not self.pnone:
            return None
        return sums.pop(), sorted(self.cand)

    def swapped_since(self, obs):
        return [k for r, w, k in obs.discards if w == "opp" and r > self.last_round]

    # ══ belief (mid_bayes) ════════════════════════════════════════════
    @staticmethod
    def opp_fair(S, rnd, board, disc, my_px):
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
            while i < len(tape) and tape[i][0] == rnd:
                _, who, px, qty = tape[i]
                i += 1
                f0 = self.opp_fair(LO, rnd, obs.board, disc, last_me)
                slope = self.opp_fair(LO + 1, rnd, obs.board, disc, last_me) - f0
                if who == "opp":
                    # a hider's quote (= public estimate) carries no information
                    if abs(px - self.public_at(obs.board, obs.discards, rnd)) >= PUB_TOL:
                        for kk, sg in enumerate(SIGMAS):
                            w = W[kk]
                            if HIDING[kk]:
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

    # ══ valuation ═════════════════════════════════════════════════════
    def expected_opp_swap(self, obs, m):
        """old_plan S9b: a sharp-style opponent swap still to come."""
        if obs.round >= 5 or obs.position == 0:
            return 0.0
        if any(who == "opp" for _, who, _ in obs.discards):
            return 0.0
        pool = sorted(r + 1 for r, c in enumerate(obs.unseen) for _ in range(c))
        n = len(pool)
        if obs.position < 0:
            card = pool[n // 6]
            return OPP_SWAP_K * (m - card) if m - card > 3 else 0.0
        card = pool[(5 * n) // 6]
        return OPP_SWAP_K * (m - card) if card - m > 3 else 0.0

    def value(self, obs, pending=None):
        """(my fair value, sd of S, identified info or None)."""
        n, tot, m, _ = self.pool(obs)
        hb = 5 - len(obs.board)
        idn = self.ident()
        if idn is not None:
            S = idn[0]
            for k in self.swapped_since(obs):     # their swap since their last quote
                S += m - k
            sd = 0.0
        else:
            S, sd = self.belief(obs, pending)
        rest = (tot - S) / max(n - 5, 1)
        V = sum(obs.hand) + sum(obs.board) + S + hb * rest + self.expected_opp_swap(obs, m)
        return V, sd, idn

    # ══ the reader model (exact, given S and t) ═══════════════════════
    @staticmethod
    def their_base(obs, S, t, P):
        """A trust-t reader's fair value (no expected-swap term)."""
        B = sum(obs.board)
        h = 5 - len(obs.board)
        D = sum(k for _, _, k in obs.discards)
        N = 47 - len(obs.board) - len(obs.discards)
        m = (DECK_SUM - S - B - D) / N
        if P is None:
            return S + B + (5 + h) * m
        return S + (1 - t) * B + t * P + m * (5 + h - t * (10 + h))

    def their_F(self, obs, S, key, P, pos=None):
        """Their fair value given my quote P (typical profile: plus the swap
        it expects from me, which depends on my position)."""
        t, sh = key
        pos = obs.position if pos is None else pos
        i_sw = any(w == "me" for _, w, _ in obs.discards)
        return self.their_base(obs, S, t, P) + self.gain(sh, obs.round, pos, i_sw)

    def model(self, obs, S, key):
        t, sh = key
        i_sw = any(w == "me" for _, w, _ in obs.discards)
        return (sh > 0, self.their_base(obs, S, t, None), self.their_base(obs, S, t, 0.0),
                t, sh, self.public_at(obs.board, obs.discards, obs.round), not i_sw)

    def events_left(self, obs):
        """Remaining quote events from this quote of mine on: ('me'/'opp', round)."""
        first = not any(r == obs.round for r, _, _, _ in obs.tape)
        ev = []
        for r in range(obs.round, 6):
            mine_first = first if (r - obs.round) % 2 == 0 else not first
            pair = ["me", "opp"] if mine_first else ["opp", "me"]
            if r == obs.round:
                pair = ["me", "opp"] if first else ["me"]
            ev += [(w, r) for w in pair]
        return ev

    def plan(self, events, pos, Pl, mdl, V):
        """Best first quote over the remaining events (absolute prices).
        Their base fair for my last quote P: Fnone if I never quoted, else A + t*P.
        Plain readers answer my quote with the fair of my PREVIOUS quote and
        quote that fair; the typical profile answers with the fair of the
        price it is answering (+-3.9 swap term) and quotes it shaded 30%
        toward the public estimate."""
        L = LIMIT
        typ, Fnone, A, t, sh, pub, gon = mdl

        def F(P):
            return Fnone if P is None else A + t * P

        def gg(r, pos):
            if not typ or not gon or r >= 5 or pos == 0:
                return 0.0
            return SHADE_G if pos > 0 else -SHADE_G

        def dfs(i, pos, Pl, depth):
            if i >= len(events):
                return 0.0, None
            who, r = events[i]
            if who == "opp":
                if typ:
                    Q = (1 - sh) * (F(Pl) + gg(r, pos)) + sh * pub
                else:
                    Q = F(Pl)
                g = 0.0
                if V - Q - 2 > RESP_MARGIN and pos < L:
                    n = min(2, L - pos)
                    g, pos = n * (V - Q - 2), pos + n
                elif Q - 2 - V > RESP_MARGIN and pos > -L:
                    n = min(2, L + pos)
                    g, pos = n * (Q - 2 - V), pos - n
                return g + dfs(i + 1, pos, Pl, depth)[0], None
            if typ:
                a, k = A + gg(r, pos), 1.0 - t

                def edge(P):
                    return a - k * P
                ok = k > 0.05
                Fl = 0.0
            else:
                Fl = F(Pl)

                def edge(P):
                    return Fl - P
                a, k, ok = Fl, 1.0, True
            opts = [V]
            if depth > 0 and ok:
                if USE_STEER:
                    opts += [(a + STEER_IN) / k, (a - STEER_IN) / k]
                if USE_HARVEST:
                    opts += [(a + HARVEST_OUT) / k, (a - HARVEST_OUT) / k]
            if depth > 0:
                if USE_LIMIT_TRICK and pos >= L:
                    opts.append(195.0)
                elif USE_LIMIT_TRICK and pos <= -L:
                    opts.append(0.0)
            best, bp = -1e18, V
            for P in opts:
                P = round(min(195.0, max(0.0, P)), 2)
                n = _lots(edge(P))                    # + they buy from me
                if n > 0:
                    n = min(n, pos + L)
                elif n < 0:
                    n = max(n, pos - L)
                if n > 0:
                    g = n * (P + 2 - V)
                elif n < 0:
                    g = -n * (V - P + 2)
                else:
                    g = 0.0
                v = g + dfs(i + 1, pos - n, P, depth - 1)[0]
                if v > best + 1e-9:
                    best, bp = v, P
            return best, bp

        return dfs(0, pos, Pl, DEPTH)

    # ══ the three calls ═══════════════════════════════════════════════
    def move(self, obs):
        try:
            return self._move(obs)
        except Exception:
            return None

    def quote(self, obs):
        try:
            return self._quote(obs)
        except Exception:
            n, tot, m, _ = self.pool(obs)
            return sum(obs.hand) + sum(obs.board) + (10 - len(obs.board)) * m

    def respond(self, obs, price):
        try:
            return self._respond(obs, price)
        except Exception:
            return 0

    def _move(self, obs):
        """old_plan S9a: swap on the expected final position, from round 3."""
        self.sync(obs)
        if any(who == "me" for _, who, _ in obs.discards) or obs.round < SWAP_FROM:
            return None
        V, _, idn = self.value(obs)
        m = self.pool(obs)[2]
        mine = [px for r, who, px, q in obs.tape if who == "me"]
        if idn is not None and not self.swapped_since(obs):
            ref = self.their_F(obs, idn[0], idn[1][len(idn[1]) // 2], mine[-1] if mine else None)
        else:
            opp_q = [px for r, who, px, q in obs.tape if who == "opp"]
            ref = opp_q[-1] if opp_q else self.public_at(obs.board, obs.discards, obs.round)
        edge = V - ref
        step = 1 if edge > 2 else (-1 if edge < -2 else 0)
        final = max(-LIMIT, min(LIMIT, obs.position + (6 - obs.round) * 2 * step))
        hand = obs.hand
        bi = max(range(5), key=lambda i: final * (m - hand[i]))
        if final * (m - hand[bi]) > SWAP_GAIN:
            return ("SWAP", bi)
        return None

    def _checked(self, obs):
        """mid_steer's check: did the reader answer my last attack quote as modelled?"""
        if self.check is None:
            return
        idx, want, pos_before = self.check
        if idx < len(obs.tape):
            q = obs.tape[idx][3]
            blocked = (want > 0 and pos_before <= -LIMIT) or (want < 0 and pos_before >= LIMIT)
            if not blocked and ((q > 0) != (want > 0) or (q < 0) != (want < 0)):
                self.off = True
            self.check = None

    def _quote(self, obs):
        self.sync(obs)
        self._checked(obs)
        V, sd, idn = self.value(obs)
        pos = obs.position
        mine = [px for r, who, px, q in obs.tape if who == "me"]
        Pl = mine[-1] if mine else None

        if idn is not None and not self.off and not self.swapped_since(obs):
            S, ts = idn
            typ = ts[0][1] > 0
            Fs = [self.their_F(obs, S, k, V if typ else Pl) for k in ts]
            same = len({k[1] for k in ts}) == 1
            if same and max(Fs) - min(Fs) < 0.02:  # their answer to this quote is exact
                key = ts[len(ts) // 2]
                _, P = self.plan(self.events_left(obs), pos, Pl, self.model(obs, S, key), V)
                if abs(P - V) > 1e-9:                # an attack quote: check the answer
                    e = self.their_F(obs, S, key, P if typ else Pl) - P
                    want = 0 if abs(e) <= 2 else (1 if e > 0 else -1)
                    self.check = (len(obs.tape), want, pos)
                    return P
                return V + random.uniform(-NOISE, NOISE)

        # the limit trick works on anyone: they cannot trade the harmful way
        if USE_LIMIT_TRICK and pos >= LIMIT:
            return 195.0
        if USE_LIMIT_TRICK and pos <= -LIMIT:
            return 0.0
        q = V
        if GUARD and self.npub and not self.nreal:
            # quote around what THEY believe (their hand = my estimate of S,
            # mine = average), skewed part of the way toward my value
            S = idn[0] if idn is not None else self.belief(obs)[0]
            m = self.pool(obs)[2]
            theirs = S + sum(obs.board) + (10 - len(obs.board)) * m
            q = theirs + max(-GSKEW_MAX, min(GSKEW_MAX, GSKEW_K * (V - theirs)))
        if SKEW and abs(pos) >= 6:
            q -= SKEW * pos
        return q + random.uniform(-NOISE, NOISE)

    def _respond(self, obs, price):
        self.sync(obs, pending=price)
        self._checked(obs)
        V, sd, idn = self.value(obs, price)
        edge = V - price
        if idn is not None and not self.swapped_since(obs):
            need = 2.0 + RESP_MARGIN
            if edge > need:
                return 2
            if edge < -need:
                return -2
            return 0
        need = 2.0 + WIDE * sd
        if abs(edge) <= need:
            return 0
        lots = int(abs(edge) - need) + 1
        return min(2, lots) * (1 if edge > 0 else -1)
