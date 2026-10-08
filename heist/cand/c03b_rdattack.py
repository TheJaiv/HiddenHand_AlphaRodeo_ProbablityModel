# Team Name: Alpha Rodeo
# Members: Jaiv Patel(26075057)
# Mentor: Arpit Gupta
# Version: candidate c03 (exact reader attack), parent versions/hunt_v14.py, idea: once two quotes of theirs fit the house reader formula exactly (trust 0.8), plan steer / harvest / limit quotes against it (our merge line's attack layer), stop at the first answer the model did not predict

"""
rival_2.py - Bayesian opponent model + a planner that exploits readers.

The stock is worth my hand + the board + the opponent's hand O, so the game is
estimating O, and knowing how the opponent estimates mine.

Inference
    A set of hypotheses about HOW the opponent forms its fair value:
        reads   does it read my quotes at all (naive vs reader)
        rule    raw / clamped to a legal hand / ignores implausible quotes /
                also reads the very price it is answering
        lam     how much of its own hand its quotes reveal (1 honest .. 0 none;
                0 also covers strategic quoters, whose quotes mean nothing)
        tau     how far it moves its estimate of my hand per lot I trade
        kappa   bias for "the opponent will swap" (ai-style bots)
    Each hypothesis carries a 2-D Gaussian over (O, trust t) updated by an
    extended Kalman filter: their quotes are noisy linear readings of their
    fair value; their responses to my quotes say their fair value is above /
    below / within 2 of my price (truncated-normal update). Hypotheses are
    reweighted by how well they predicted what happened; outliers are expected.

Decisions
    Every candidate action (a price to quote; buy / pass / sell) is scored as
    the expected profit now plus a play-out of the rest of the deal under the
    top hypotheses, through a concave (square-root-like) utility, as the score.
    Readers believe my quotes, which makes them steerable:
      * at +-10 lots my quote cannot be traded against in the bad direction,
        so an extreme price is free. A reader then thinks the stock is worth
        ~170 (or ~20) and trades into my position at absurd prices.
      * a paid "probe" (a quote implying a hand of 63 or 7) is only used once
        the opponent is clearly a reader with informative quotes, and only
        when its next quote will show whether the probe worked.
    Swap: lowest card if I expect to end long, highest if short, when the
    expected final position x (new card - old card) is large enough.
"""

import math

MAXP = 195.0
SQ2 = math.sqrt(2.0)
ISQ2PI = 1.0 / math.sqrt(2.0 * math.pi)
INF = float("inf")

RAW, CLAMP, SANE, CUR, BLD = 0, 1, 2, 3, 4
P_NAIVE = 0.6
P_BLEND = 0.12      # prior mass of blend quoters (the rest scaled by 1 - P_BLEND)
BLEND_LAM = ((1.0, 0.5), (0.7, 0.2), (0.4, 0.15), (0.2, 0.15))
BLEND_SK = ((0.0, 0.5), (0.9, 0.5))   # their quote skew per lot of MY position
W_MEAN, W_SD = 0.45, 0.25
BLEND_TAU = ((0.0, 0.3), (1.5, 0.4), (3.0, 0.3))
CARRY = 0.82      # how much a board card moves a carried fair, per point off 7
RULE_PRIOR = {RAW: 0.55, CLAMP: 0.2, SANE: 0.08, CUR: 0.17}
LAM_PRIOR = ((1.0, 0.45), (0.7, 0.12), (0.4, 0.08), (0.0, 0.35))
TAU_PRIOR = ((0.0, 0.6), (1.5, 0.25), (3.0, 0.15))      # only for honest quoters
KAP_PRIOR = ((0.0, 0.8), (3.9, 0.2))
T_MEAN, T_SD = 0.6, 0.3

SIG_Q = 0.5       # quote model noise
EPS_Q = 0.1       # chance a quote is unexplained
U_Q = 0.02        # density of an unexplained quote
SIG_R = 1.0       # response threshold noise
EPS_R = 0.06      # chance a response is unexplained
PRUNE = 12.0      # drop hypotheses this many log-units behind the best
SWAP_TH = (15.0, 12.0, 9.0, 6.0, 4.0)   # by round: waiting has option value
DELTAS = (2.0, 2.5, 3.0, 3.5, 4.5, 6.0)
NPLAN = 6         # hypotheses used in play-outs
P_EXT = 0.9       # confidence in a raw reader needed to PAY for an extreme quote
EX_TOL = 0.02      # exact-reader test: every quote within this of the house reader formula
P_PROBE = 0.85    # confidence in any reader needed to pay for a probe (implied 63 / 7)
LAM_PROBE = 0.4   # ... and only if its quotes are informative (strategic quoters are not)
RISK = 60.0       # utility curvature

# hypothesis fields
H_READS, H_RULE, H_LAM, H_TAU, H_KAP, H_MO, H_MT, H_P00, H_P01, H_P11, H_LW, H_SK = range(12)


def Phi(x):
    return 0.5 * (1.0 + math.erf(x / SQ2))


def pdf(x):
    return math.exp(-0.5 * x * x) * ISQ2PI


def util(x):
    """Concave utility: linear for small PnL, square-root-like for large."""
    return x / math.sqrt(1.0 + abs(x) / RISK)


def coefs(st, reads, rule, q, L):
    """Opponent fair = A0 + A1*t + (B0 + B1*t)*O, before tau / kappa terms.

    st: (bv, hb, npk, pk, N, C0, mo) public state; q: my quote it reads (None
    for none); L: the clamped implied hand, or None.
    """
    bv, hb, npk, pk, N, C0, mo = st
    cm0 = 5 - npk + hb
    A0 = bv + pk + cm0 * C0 / N
    B0 = 1 - cm0 / N
    if not reads or q is None:
        return A0, 0.0, B0, 0.0
    if L is None:
        c1 = 10 - npk + hb
        return A0, (q - bv - pk) - c1 * C0 / N, B0, c1 / N
    c1 = 5 - npk
    return A0, (L - pk) - c1 * C0 / N, B0, c1 / N


def implied(st, q):
    return q - st[0] - (5 + st[1]) * st[6]


def pick_q(st, rule, mq):
    """Which of my quotes (newest last) a reader of this rule uses, and clamp."""
    if not mq:
        return None, None
    if rule == SANE:
        for x in reversed(mq):
            if 12 <= implied(st, x) <= 58:
                return x, None
        return None, None
    q = mq[-1]
    if rule == CLAMP:
        imp = implied(st, q)
        if imp > 65:
            return q, 65.0
        if imp < 5:
            return q, 5.0
    return q, None


def ekf(h, Ho, Ht, d, S, Vy):
    """Kalman step for hypothesis h: a reading with gradient (Ho, Ht) in (O, t)
    and predictive variance S came out d above its prediction; Vy is what is
    left of its variance afterwards (0 when it was seen exactly).
    Returns the new (mean O, mean t, P00, P01, P11)."""
    P00, P01, P11 = h[H_P00], h[H_P01], h[H_P11]
    PHo = P00 * Ho + P01 * Ht
    PHt = P01 * Ho + P11 * Ht
    k0 = PHo / S
    k1 = PHt / S
    g = S - Vy
    return (h[H_MO] + k0 * d, h[H_MT] + k1 * d,
            P00 - g * k0 * k0, P01 - g * k0 * k1, P11 - g * k1 * k1)


def mix_into(h, r, new):
    """Moment-match r*new + (1-r)*old into h."""
    m0, m1, a, b, c = new
    o0, o1 = h[H_MO], h[H_MT]
    n0 = r * m0 + (1 - r) * o0
    n1 = r * m1 + (1 - r) * o1
    h[H_P00] = max(0.05, r * (a + m0 * m0) + (1 - r) * (h[H_P00] + o0 * o0) - n0 * n0)
    h[H_P01] = r * (b + m0 * m1) + (1 - r) * (h[H_P01] + o0 * o1) - n0 * n1
    h[H_P11] = max(1e-5, r * (c + m1 * m1) + (1 - r) * (h[H_P11] + o1 * o1) - n1 * n1)
    h[H_MO] = n0
    h[H_MT] = min(1.15, max(0.0, n1))
    lim = math.sqrt(h[H_P00] * h[H_P11]) * 0.999
    if h[H_P01] > lim:
        h[H_P01] = lim
    elif h[H_P01] < -lim:
        h[H_P01] = -lim


# ── exact house-reader attack ───────────────────────────────────────────────
# The house reader and sharp quote fair = S + (1-T)*board + T*P + m*(5 + h - T*(10 + h)) with
# T = 0.8 and P = my last quote, rounded to 0.01. Once two of their quotes (one of them reading
# a quote of mine) give the same whole hand sum S, they are steered and harvested with an exact
# look-ahead (our merge line's attack layer). The first answer that differs from the model
# switches the attack off for the rest of the deal.
DECK_SUM = 364
RD_T = 0.8          # the house reader / sharp trust in my last quote
RD_TOL = 0.0051     # their quotes are rounded to 0.01
RD_NQ = 2           # consistent quotes needed, at least one of them reading a quote of mine
STEER_IN = 1.98     # inside their +-2 band: no trade, their belief moves
HARVEST_OUT = 3.02  # outside it: sharp's sizing gives 2 lots at edge >= 3
RESP_MARGIN = 0.2   # extra edge wanted when answering an identified reader
DEPTH = 4           # quotes of mine explored with every option
LIMIT = 10


def _lots(e):
    """sharp's sizing for a taker with edge e: signed lots (+ buy)."""
    a = abs(e)
    if a <= 2:
        return 0
    n = min(2, int(a - 2) + 1)
    return n if e > 0 else -n


class _Reader:
    """Identifies an exact house reader and plans quotes against it."""

    def __init__(self):
        self.S = None        # hand sum of the current run of consistent quotes
        self.nq = 0          # consistent quotes in that run
        self.nread = 0       # ... of them made after a quote of mine
        self.done = 0        # their quotes processed
        self.last_round = 0
        self.peeked = False
        self.off = False     # an answer did not fit the model
        self.check = None    # (tape index, expected sign of their qty, my position then)

    @staticmethod
    def invert(F, B, h, D, N, P):
        U0 = DECK_SUM - B - D
        if P is None:
            c0, c1 = B, 5 + h
        else:
            c0, c1 = (1 - RD_T) * B + RD_T * P, 5 + h - RD_T * (10 + h)
        a = 1 - c1 / N
        S = round((F - c0 - c1 * U0 / N) / a)
        if not 5 <= S <= 65:
            return None
        pred = S + c0 + c1 * (U0 - S) / N
        return S if abs(pred - F) <= RD_TOL else None

    def observe(self, F, rnd, obs, P):
        self.done += 1
        if self.peeked:
            return
        B, h = sum(obs.board[:rnd - 1]), 5 - (rnd - 1)
        ds = [(r, w, k) for r, w, k in obs.discards if r <= rnd]
        D, N = sum(k for _, _, k in ds), 47 - (rnd - 1) - len(ds)
        olds = [k for r, w, k in ds if w == "opp" and r > self.last_round]
        self.last_round = rnd
        S = self.invert(F, B, h, D, N, P)
        if S is not None and self.S is not None:
            if olds:
                lo = self.S - olds[0]
                ok = lo + 1 <= S <= lo + 13
            else:
                ok = S == self.S
            if ok:
                self.S = S
                self.nq += 1
                self.nread += P is not None
                return
        self.S = S
        self.nq = 1 if S is not None else 0
        self.nread = 1 if (S is not None and P is not None) else 0

    def sync(self, obs, pending=None):
        if any(w == "opp" for _, w in obs.peeks):
            self.peeked = True
        quotes, P = [], None
        for r, who, px, q in obs.tape:
            if who == "me":
                P = px
            else:
                quotes.append((px, r, P))
        if pending is not None:
            quotes.append((pending, obs.round, P))
        for px, r, p in quotes[self.done:]:
            self.observe(px, r, obs, p)
        if self.check is not None:
            idx, want, pos_before = self.check
            if idx < len(obs.tape):
                q = obs.tape[idx][3]
                blocked = (want > 0 and pos_before <= -LIMIT) or (want < 0 and pos_before >= LIMIT)
                if not blocked and ((q > 0) != (want > 0) or (q < 0) != (want < 0)):
                    self.off = True
                self.check = None

    def active(self, obs):
        if self.off or self.peeked or self.S is None or self.nq < RD_NQ or self.nread < 1:
            return False
        return not any(w == "opp" and r > self.last_round for r, w, k in obs.discards)

    def value(self, obs):
        n = sum(obs.unseen)
        tot = sum((r + 1) * c for r, c in enumerate(obs.unseen))
        rest = (tot - self.S) / max(n - 5, 1)
        return sum(obs.hand) + sum(obs.board) + self.S + (5 - len(obs.board)) * rest

    @staticmethod
    def their_base(obs, S, P):
        B = sum(obs.board)
        h = 5 - len(obs.board)
        D = sum(k for _, _, k in obs.discards)
        N = 47 - len(obs.board) - len(obs.discards)
        m = (DECK_SUM - S - B - D) / N
        if P is None:
            return S + B + (5 + h) * m
        return S + (1 - RD_T) * B + RD_T * P + m * (5 + h - RD_T * (10 + h))

    @staticmethod
    def events_left(obs):
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

    def plan(self, events, pos, Pl, Fnone, A, V):
        """Best first quote over the remaining events (exact reader model)."""
        L = LIMIT
        t = RD_T

        def F(P):
            return Fnone if P is None else A + t * P

        memo = {}

        def dfs(i, pos, Pl, depth):
            if i >= len(events):
                return 0.0, None
            key = (i, pos, Pl, depth)
            got = memo.get(key)
            if got is not None:
                return got
            got = memo[key] = step(i, pos, Pl, depth)
            return got

        def step(i, pos, Pl, depth):
            who, r = events[i]
            if who == "opp":
                Q = F(Pl)
                g = 0.0
                if V - Q - 2 > RESP_MARGIN and pos < L:
                    n = min(2, L - pos)
                    g, pos = n * (V - Q - 2), pos + n
                elif Q - 2 - V > RESP_MARGIN and pos > -L:
                    n = min(2, L + pos)
                    g, pos = n * (Q - 2 - V), pos - n
                return g + dfs(i + 1, pos, Pl, depth)[0], None
            Fl = F(Pl)
            opts = [V]
            if depth > 0:
                opts += [Fl + STEER_IN, Fl - STEER_IN, Fl + HARVEST_OUT, Fl - HARVEST_OUT, 195.0, 0.0]
            best, bp = -1e18, V
            for P in opts:
                P = round(min(195.0, max(0.0, P)), 2)
                n = _lots(Fl - P)                     # + they buy from me
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

        return dfs(0, pos, Pl, DEPTH if len(events) < 7 else DEPTH - 1)   # keeps round 2 fast

    def quote(self, obs):
        V = self.value(obs)
        mine = [px for r, who, px, q in obs.tape if who == "me"]
        Pl = mine[-1] if mine else None
        Fnone = self.their_base(obs, self.S, None)
        A = self.their_base(obs, self.S, 0.0)
        _, P = self.plan(self.events_left(obs), obs.position, Pl, Fnone, A, V)
        if abs(P - V) > 1e-9:
            e = (Fnone if Pl is None else A + RD_T * Pl) - P
            want = 0 if abs(e) <= 2 else (1 if e > 0 else -1)
            self.check = (len(obs.tape), want, obs.position)
        return P

    def respond(self, obs, price):
        edge = self.value(obs) - price
        need = 2.0 + RESP_MARGIN
        return 2 if edge > need else (-2 if edge < -need else 0)


class Bot:
    def __init__(self):
        self.H = None        # hypotheses
        self.done = 0        # tape entries consumed
        self.ndisc = 0       # discards consumed
        self.extra = -1      # tape slot of their quote consumed early
        self.first = None    # do I quote first in odd rounds?
        self.rd = _Reader()  # exact house-reader attack

    # ── inference ──────────────────────────────────────────────
    def _init(self, obs):
        u = obs.unseen
        U = sum(u)
        S = sum((r + 1) * c for r, c in enumerate(u))
        m = S / U
        v = sum(c * (r + 1 - m) ** 2 for r, c in enumerate(u)) / U
        mu = 5 * m
        var = 5 * v * (U - 5) / (U - 1)
        self.obar = mu
        H = []
        combos = [(False, RAW, P_NAIVE)] + [(True, r, (1 - P_NAIVE) * p) for r, p in RULE_PRIOR.items()]
        for reads, rule, pr in combos:
            for lam, pl in LAM_PRIOR:
                for tau, pt in TAU_PRIOR:
                    if tau and lam < 1:
                        continue
                    if lam < 1:
                        pt = 1.0
                    for kap, pk in KAP_PRIOR:
                        lw = math.log((1 - P_BLEND) * pr * pl * pt * pk)
                        H.append([reads, rule, lam, tau, kap, mu, T_MEAN if reads else 0.0,
                                  var, 0.0, T_SD * T_SD if reads else 1e-6, lw, 0.0])
        for lam, pl in BLEND_LAM:
            for tau, pt in BLEND_TAU:
                for kap, pk in KAP_PRIOR:
                    for sk, ps in BLEND_SK:
                        lw = math.log(P_BLEND * pl * pt * pk * ps)
                        H.append([False, BLD, lam, tau, kap, mu, W_MEAN,
                                  var, 0.0, W_SD * W_SD, lw, sk])
        self.H = H

    def _prune(self):
        best = max(h[H_LW] for h in self.H)
        self.H = [h for h in self.H if h[H_LW] > best - PRUNE]
        for h in self.H:
            h[H_LW] -= best

    @staticmethod
    def _state(obs, r, obar):
        """Public state as the opponent saw it in round r."""
        board = obs.board[:r - 1]
        nb = len(board)
        bv = sum(board)
        nd = 0
        ds = 0
        for d in obs.discards:
            if d[0] <= r:
                nd += 1
                ds += d[2]
        npk = 0
        for p in obs.peeks:
            if p[1] == "opp" and p[0] <= r:
                npk += 1
        npk = min(npk, 5)
        pk = npk * sum(obs.hand) / 5.0
        N = 47 - nb - nd - npk
        C0 = 364 - bv - ds - pk
        return (bv, 5 - nb, npk, pk, N, C0, (C0 - obar) / N)

    @staticmethod
    def _before(tape, j):
        """My position and my net lots bought at their quotes, before slot j."""
        pos = 0
        Q = 0
        for k in range(j):
            r, who, price, qty = tape[k]
            if who == "me":
                pos -= qty
            else:
                pos += qty
                Q += qty
        return pos, Q

    @staticmethod
    def _ks(obs, r, pos):
        """Sign used by swap-expecting bots: my position, if I may still swap."""
        if r >= 5 or pos == 0:
            return 0
        for d in obs.discards:
            if d[1] == "me" and d[0] <= r:
                return 0
        return 1 if pos > 0 else -1

    @staticmethod
    def _lastq(obs, j, r):
        """My last quote before tape slot j, carried to round r the way a
        blend quoter carries it (board cards and my swaps since), or None."""
        tape = obs.tape
        k = min(j, len(tape)) - 1
        while k >= 0 and tape[k][1] != "me":
            k -= 1
        if k < 0:
            return None
        rq, q = tape[k][0], tape[k][2]
        for c in obs.board[rq - 1:r - 1]:
            q += CARRY * (c - 7.0)
        for d in obs.discards:
            if d[1] == "me" and rq < d[0] <= r:
                q += 7.0 - d[2]
        return q

    def _see(self, obs, r, j, price, qty, is_quote):
        tape = obs.tape
        st = self._state(obs, r, self.obar)
        pos, Q = self._before(tape, j)
        ks = self._ks(obs, r, pos)
        mq = [tape[k][2] for k in range(min(j, len(tape))) if tape[k][1] == "me"]
        mqc = mq + [price] if not is_quote else mq
        if not is_quote:
            can_buy = pos > -10
            can_sell = pos < 10
            if qty > 0:
                lo, hi = price + 2, INF
            elif qty < 0:
                lo, hi = -INF, price - 2
            else:
                lo = price - 2 if can_sell else -INF
                hi = price + 2 if can_buy else INF
                if lo == -INF and hi == INF:
                    return
        cof = {}
        lq = self._lastq(obs, j, r) if is_quote else None
        for h in self.H:
            reads, rule, lam = h[H_READS], h[H_RULE], h[H_LAM]
            if is_quote and lam == 0:
                h[H_LW] += math.log(U_Q)
                continue
            key = (reads, rule)
            c = cof.get(key)
            if c is None:
                src = mqc if (rule == CUR and not is_quote) else mq
                q, L = pick_q(st, rule, src)
                c = cof[key] = coefs(st, reads, rule, q, L)
            A0, A1, B0, B1 = c
            mo, mt = h[H_MO], h[H_MT]
            extra = h[H_TAU] * Q + h[H_KAP] * ks
            if is_quote:
                oe = lam * mo + (1 - lam) * self.obar
                if rule == BLD:
                    F = A0 + B0 * oe + extra
                    if lq is None:
                        pred, Ho, Ht = F, B0 * lam, 0.0
                    else:
                        F += h[H_SK] * pos
                        pred = (1 - mt) * F + mt * lq
                        Ho = (1 - mt) * B0 * lam
                        Ht = lq - F
                else:
                    pred = A0 + A1 * mt + (B0 + B1 * mt) * oe + extra
                    Ho = (B0 + B1 * mt) * lam
                    Ht = A1 + B1 * oe
                S = (h[H_P00] * Ho * Ho + 2 * h[H_P01] * Ho * Ht + h[H_P11] * Ht * Ht
                     + SIG_Q * SIG_Q)
                d = price - pred
                dens = math.exp(-d * d / (2 * S)) * ISQ2PI / math.sqrt(S)
                ev = (1 - EPS_Q) * dens + EPS_Q * U_Q
                rr = (1 - EPS_Q) * dens / ev
                mix_into(h, rr, ekf(h, Ho, Ht, d, S, 0.0))
                h[H_LW] += math.log(ev)
            else:
                my = A0 + A1 * mt + (B0 + B1 * mt) * mo + extra
                Ho = B0 + B1 * mt
                Ht = A1 + B1 * mo
                S = (h[H_P00] * Ho * Ho + 2 * h[H_P01] * Ho * Ht + h[H_P11] * Ht * Ht
                     + SIG_R * SIG_R)
                sy = math.sqrt(S)
                if lo == -INF:
                    al, pa, Fa, ta = -INF, 0.0, 0.0, 0.0
                else:
                    al = (lo - my) / sy
                    pa, Fa = pdf(al), Phi(al)
                    ta = al * pa
                if hi == INF:
                    pb, Fb, tb = 0.0, 1.0, 0.0
                else:
                    be = (hi - my) / sy
                    pb, Fb = pdf(be), Phi(be)
                    tb = be * pb
                Z = Fb - Fa
                ev = (1 - EPS_R) * Z + EPS_R / 3.0
                h[H_LW] += math.log(ev)
                if Z < 1e-9:
                    continue
                rr = (1 - EPS_R) * Z / ev
                m1 = (pa - pb) / Z
                vy = S * (1 + (ta - tb) / Z - m1 * m1)
                mix_into(h, rr, ekf(h, Ho, Ht, sy * m1, S, vy))
        self._prune()

    def _see_swap(self, obs, card):
        u = obs.unseen
        U = sum(u)
        m = sum((r + 1) * c for r, c in enumerate(u)) / U
        v = sum(c * (r + 1 - m) ** 2 for r, c in enumerate(u)) / U
        for h in self.H:
            h[H_MO] += m - card
            h[H_P00] += v

    def _sync(self, obs, cur=None):
        if self.H is None:
            self._init(obs)
        tape = obs.tape
        disc = obs.discards
        while True:
            nd = disc[self.ndisc] if self.ndisc < len(disc) else None
            nt = tape[self.done] if self.done < len(tape) else None
            if nd is None and nt is None:
                break
            if nd is not None and (nt is None or nd[0] <= nt[0]):
                if nd[1] == "opp":
                    self._see_swap(obs, nd[2])
                self.ndisc += 1
                continue
            j = self.done
            self.done += 1
            if j == self.extra:
                continue
            r, who, price, qty = nt
            if who == "opp":
                if 0.0 < price < MAXP:
                    self._see(obs, r, j, price, 0, True)
            else:
                self._see(obs, r, j, price, qty, False)
        if cur is not None:
            j = len(tape)
            if 0.0 < cur < MAXP:
                self._see(obs, obs.round, j, cur, 0, True)
            self.extra = j

    def _ev(self, obs):
        """E[V | O] = alpha + beta * O."""
        u = obs.unseen
        U = sum(u)
        S = sum((r + 1) * c for r, c in enumerate(u))
        k = 5 - len(obs.opp_known)
        kn = sum(obs.opp_known)
        hb = 5 - len(obs.board)
        den = U - k
        alpha = sum(obs.hand) + sum(obs.board) + hb * (S + kn) / den
        beta = 1 - hb / den
        return alpha, beta

    def _mo(self):
        tw = 0.0
        tm = 0.0
        for h in self.H:
            w = math.exp(h[H_LW])
            tw += w
            tm += w * h[H_MO]
        return tm / tw

    def _p_reader(self):
        """P(reads my quotes with trust >= 0.5), P(... and without a clamp)."""
        tw = 0.0
        trd = 0.0
        trw = 0.0
        for h in self.H:
            w = math.exp(h[H_LW])
            tw += w
            if h[H_READS] and h[H_MT] >= 0.5 and h[H_LAM] >= LAM_PROBE:
                trd += w
                if h[H_RULE] in (RAW, CUR):
                    trw += w
        return trd / tw, trw / tw

    def _exact_reader(self, obs):
        """Trust t if their quotes since their last swap (3 or more) fit the house
        reader formula exactly (raw reading of my last quote, one trust t, no
        trade or swap terms), else None."""
        last_swap = 0
        for d in obs.discards:
            if d[1] == "opp" and d[0] > last_swap:
                last_swap = d[0]
        rows = []
        lastq = None
        for r, who, price, qty in obs.tape:
            if who == "me":
                lastq = price
                continue
            if r < last_swap or not 0.0 < price < MAXP:
                continue
            rows.append((price,) + coefs(self._state(obs, r, self.obar), True, RAW, lastq, None))
        if len(rows) < 3:
            return None
        best, bt = None, None
        for i in range(231):
            t = i * 0.005
            num = 0.0
            den = 0.0
            for q, A0, A1, B0, B1 in rows:
                b = B0 + B1 * t
                num += (q - A0 - A1 * t) * b
                den += b * b
            O = num / den
            err = 0.0
            for q, A0, A1, B0, B1 in rows:
                e = abs(q - A0 - A1 * t - (B0 + B1 * t) * O)
                if e > err:
                    err = e
            if best is None or err < best:
                best, bt = err, t
        return bt if best < EX_TOL else None

    # ── planning ──────────────────────────────────────────────
    @staticmethod
    def _slots(first, start):
        """Quote slots start..9 as (I am the maker, round). Each round has two
        slots; I quote first in odd rounds iff `first`."""
        out = []
        for s in range(start, 10):
            r = s // 2 + 1
            me_first = (r % 2 == 1) == first
            out.append(((s % 2 == 0) == me_first, r))
        return out

    def _bel(self, st, h, O, q, Q, ks):
        """Opponent fair under hypothesis h (point estimates) reading my quote q."""
        L = None
        if q is not None and h[H_READS]:
            rule = h[H_RULE]
            if rule == SANE:
                if not 12 <= implied(st, q) <= 58:
                    q = None
            elif rule == CLAMP:
                imp = implied(st, q)
                if imp > 65:
                    L = 65.0
                elif imp < 5:
                    L = 5.0
        A0, A1, B0, B1 = coefs(st, h[H_READS], h[H_RULE], q, L)
        t = h[H_MT]
        return A0 + A1 * t + (B0 + B1 * t) * O + h[H_TAU] * Q + h[H_KAP] * ks, B0 + B1 * t

    def _roll(self, st, h, V, pos, Q, qeff, slots, swapped, lq=None):
        """Deterministic play-out of `slots` under hypothesis h, with simple
        rules for me (trade against their belief, extreme quote at +-10).
        Returns (profit relative to value V, final position)."""
        O = h[H_MO]
        lam = h[H_LAM]
        reads = h[H_READS]
        rule = h[H_RULE]
        cur_rule = reads and rule == CUR
        bld = rule == BLD
        W = h[H_MT]
        sk = h[H_SK]
        pnl = 0.0
        for me, r in slots:
            ks = 0 if (swapped or r >= 5 or pos == 0) else (1 if pos > 0 else -1)
            f, b = self._bel(st, h, O, qeff, Q, ks)
            if me:
                if pos >= 10:
                    p = MAXP
                elif pos <= -10:
                    p = 0.0
                elif f > V + 1:
                    p = f - 3.05
                elif f < V - 1:
                    p = f + 3.05
                else:
                    p = f
                if cur_rule:
                    f, b = self._bel(st, h, O, p, Q, ks)
                e = f - p
                if e > 2:
                    n = min(2, 10 + pos)
                    pos -= n
                    pnl += n * (p + 2 - V)
                elif e < -2:
                    n = min(2, 10 - pos)
                    pos += n
                    pnl += n * (V - p + 2)
                if reads and (rule != SANE or 12 <= implied(st, p) <= 58):
                    qeff = p
                lq = p
            elif lam > 0:
                q = f - b * (1 - lam) * (O - self.obar)
                if bld and lq is not None:
                    q = (1 - W) * (q + sk * pos) + W * lq
                if V - q - 2 > 0:
                    n = min(2, 10 - pos)
                    pos += n
                    Q += n
                    pnl += n * (V - q - 2)
                elif q - 2 - V > 0:
                    n = min(2, 10 + pos)
                    pos -= n
                    Q -= n
                    pnl += n * (q - 2 - V)
        return pnl, pos

    def _plan_setup(self, obs, k):
        st = self._state(obs, obs.round, self.obar)
        hs = sorted(self.H, key=lambda h: -h[H_LW])[:NPLAN]
        ws = [math.exp(h[H_LW]) for h in hs]
        tw = sum(ws)
        ws = [w / tw for w in ws]
        mq = [e[2] for e in obs.tape if e[1] == "me"]
        qe = {}
        for rule in (RAW, CLAMP, SANE, CUR, BLD):
            q = pick_q(st, rule, mq)[0]
            qe[rule] = q
        swapped = any(d[1] == "me" for d in obs.discards)
        return st, hs, ws, qe, self._slots(self.first, k + 1), swapped

    # ── the three methods the engine calls ───────────────────────
    @staticmethod
    def _plain_fair(obs):
        """Card-counting value, used only if something goes wrong."""
        u = obs.unseen
        m = sum((r + 1) * c for r, c in enumerate(u)) / max(1, sum(u))
        hidden = 10 - len(obs.opp_known) - len(obs.board)
        return sum(obs.hand) + sum(obs.board) + sum(obs.opp_known) + hidden * m

    def quote(self, obs):
        try:
            q = self._quote(obs)
        except Exception:
            q = self._plain_fair(obs)
        try:
            self.rd.sync(obs)
            if self.rd.active(obs):
                return self.rd.quote(obs)
        except Exception:
            self.rd.off = True
        return q

    def respond(self, obs, price):
        try:
            a = self._respond(obs, price)
        except Exception:
            e = self._plain_fair(obs) - price
            a = 2 if e > 2 else (-2 if e < -2 else 0)
        try:
            self.rd.sync(obs, price)
            if self.rd.active(obs):
                return self.rd.respond(obs, price)
        except Exception:
            self.rd.off = True
        return a

    def move(self, obs):
        try:
            return self._move(obs)
        except Exception:
            return None

    def _quote(self, obs):
        self._sync(obs)
        tape = obs.tape
        j = len(tape)
        if self.first is None:
            self.first = (j == 0)
        pos = obs.position
        _, Q = self._before(tape, j)
        alpha, beta = self._ev(obs)
        st, hs, ws, qe, slots, swapped = self._plan_setup(obs, j)
        ks = self._ks(obs, obs.round, pos)
        cur = obs.cash - obs.spent
        nb = min(2, 10 + pos)
        ns = min(2, 10 - pos)
        comps = []
        for w, h in zip(ws, hs):
            V = alpha + beta * h[H_MO]
            comps.append((w, h, V))

        def resp_dist(h, p):
            """Mean, sd and cov(O, .)/sd of their fair when answering price p."""
            q = p if (h[H_READS] and h[H_RULE] == CUR) else qe[h[H_RULE]]
            f, _ = self._bel(st, h, h[H_MO], q, Q, ks)
            L = None
            if q is not None and h[H_READS] and h[H_RULE] == CLAMP:
                imp = implied(st, q)
                L = 65.0 if imp > 65 else (5.0 if imp < 5 else None)
            if q is not None and h[H_READS] and h[H_RULE] == SANE and not 12 <= implied(st, q) <= 58:
                q = None
            A0, A1, B0, B1 = coefs(st, h[H_READS], h[H_RULE], q, L)
            Ho = B0 + B1 * h[H_MT]
            Ht = A1 + B1 * h[H_MO]
            cO = h[H_P00] * Ho + h[H_P01] * Ht
            S = cO * Ho + (h[H_P01] * Ho + h[H_P11] * Ht) * Ht + SIG_R * SIG_R
            sf = math.sqrt(S)
            return f, sf, cO / sf

        def imm(h, V, p):
            f, sf, c = resp_dist(h, p)
            zb = (f - p - 2) / sf
            zs = (p - 2 - f) / sf
            return (nb * ((p + 2 - V) * Phi(zb) - beta * c * pdf(zb))
                    + ns * ((V - p + 2) * Phi(zs) - beta * c * pdf(zs))), f

        # the best price for this trade alone (risk-neutral)
        f0 = [resp_dist(h, comps[0][2])[0] for _, h, _ in comps[:2]]
        cands = set()
        for f in f0:
            for d in DELTAS:
                cands.add(f + d)
                cands.add(f - d)
        best, bp = 0.0, f0[0]
        for p in cands:
            v = 0.0
            for w, h, V in comps:
                v += w * imm(h, V, p)[0]
            if v > best:
                best, bp = v, p
        # then weigh what each candidate does to the rest of the deal
        cands = [bp, f0[0], f0[0] + 3.05, f0[0] - 3.05]
        imp0 = st[0] + (5 + st[1]) * st[6]
        if pos >= 10:
            cands += [MAXP, imp0 + 65.0, imp0 + 58.0]
        elif pos <= -10:
            cands += [0.0, imp0 + 5.0, imp0 + 12.0]
        elif obs.round <= 4 and slots and 0.79 <= (self._exact_reader(obs) or 0.0) <= 0.81:
            cands += [MAXP, 0.0]
        elif slots and not slots[0][0]:
            # paid manipulation only when their next quote shows whether it worked
            p_rd, p_raw = self._p_reader()
            if p_raw >= P_EXT:
                cands += [MAXP, 0.0]
            if p_rd >= P_PROBE:
                cands += [imp0 + 63.0, imp0 + 7.0, imp0 + 55.0, imp0 + 15.0]
        bestv, bestp = None, bp
        for p in cands:
            p = min(MAXP, max(0.0, p))
            v = 0.0
            for w, h, V in comps:
                x, f = imm(h, V, p)
                e = f - p
                ps = pos
                if e > 2:
                    ps -= nb
                elif e < -2:
                    ps += ns
                qeff = p if h[H_READS] else None
                if h[H_READS] and h[H_RULE] == SANE and not 12 <= implied(st, p) <= 58:
                    qeff = qe[SANE]
                x += self._roll(st, h, V, ps, Q, qeff, slots, swapped, p)[0]
                v += w * util(cur + pos * V + x)
            if bestv is None or v > bestv:
                bestv, bestp = v, p
        return min(MAXP, max(0.0, bestp))

    def _respond(self, obs, price):
        self._sync(obs, price)
        tape = obs.tape
        j = len(tape)
        if self.first is None:
            self.first = (j != 0)
        pos = obs.position
        _, Q = self._before(tape, j)
        alpha, beta = self._ev(obs)
        st, hs, ws, qe, slots, swapped = self._plan_setup(obs, j)
        cur = obs.cash - obs.spent
        lq = self._lastq(obs, j, obs.round)
        nbuy = min(2, 10 - pos)
        nsell = min(2, 10 + pos)
        best, bq = None, 0
        for qty in (0, nbuy, -nsell):
            v = 0.0
            for w, h in zip(ws, hs):
                V = alpha + beta * h[H_MO]
                if qty > 0:
                    x = qty * (V - price - 2)
                elif qty < 0:
                    x = -qty * (price - 2 - V)
                else:
                    x = 0.0
                qeff = qe[h[H_RULE]] if h[H_READS] else None
                x += self._roll(st, h, V, pos + qty, Q + qty, qeff, slots, swapped, lq)[0]
                v += w * util(cur + pos * V + x)
            if best is None or v > best + 1e-9:
                best, bq = v, qty
        return bq

    def _move(self, obs):
        self._sync(obs)
        if any(w == "me" for _, w, _ in obs.discards):
            return None
        pos = obs.position
        r = obs.round
        # expected final position, from play-outs of the rest of the deal
        st = self._state(obs, r, self.obar)
        hs = sorted(self.H, key=lambda h: -h[H_LW])[:NPLAN]
        ws = [math.exp(h[H_LW]) for h in hs]
        tw = sum(ws)
        alpha, beta = self._ev(obs)
        _, Q = self._before(obs.tape, len(obs.tape))
        mq = [e[2] for e in obs.tape if e[1] == "me"]
        qe = {rule: pick_q(st, rule, mq)[0] for rule in (RAW, CLAMP, SANE, CUR, BLD)}
        seats = (self.first,) if self.first is not None else (True, False)
        fpos = 0.0
        lq = self._lastq(obs, len(obs.tape), r)
        for first in seats:
            slots = self._slots(first, 2 * (r - 1))
            for w, h in zip(ws, hs):
                V = alpha + beta * h[H_MO]
                qeff = qe[h[H_RULE]] if h[H_READS] else None
                fpos += w * self._roll(st, h, V, pos, Q, qeff, slots, False, lq)[1]
        fpos /= tw * len(seats)
        u = obs.unseen
        U = sum(u)
        S = sum((rk + 1) * c for rk, c in enumerate(u))
        k = 5 - len(obs.opp_known)
        eo = self._mo() - sum(obs.opp_known)
        mstack = (S - eo) / (U - k)
        hand = obs.hand
        if fpos > 0:
            i = min(range(5), key=lambda x: hand[x])
            gain = fpos * (mstack - hand[i])
        else:
            i = max(range(5), key=lambda x: hand[x])
            gain = fpos * (mstack - hand[i])
        if gain > SWAP_TH[r - 1]:
            return ("SWAP", i)
        return None
