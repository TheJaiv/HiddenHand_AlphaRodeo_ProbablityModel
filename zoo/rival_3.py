# Team Name: Alpha Rodeo
# Members: Jaiv Patel
# Mentor: Arpit Gupta

"""
rival_3.py - Bayesian opponent modelling plus a short look-ahead planner.

1. WHO IS THE OPPONENT, AND WHAT DO THEY HOLD?
   A joint posterior over (opponent model, opponent hand sum S), S = 5..65.
   Most bots quote their own fair value, and a fair value is a linear
   function of the hand sum, so one quote pins S down almost exactly. Models:
     rfree   - the reader family (naive, reader, sharp and any TRUST): quotes
               its fair value, reading our last quote with trust t. t is
               solved per S from their quotes, then checked on later quotes.
     hider / ai / liar - quote the public estimate, shade towards it, or
               mirror their hand early. Exact formulas.
     gen / genflat - catch-alls with wide noise, for anything else.
   Their trades (buy / sell / pass on our quotes) are evidence too, and so
   are their swaps (S changes by a known discard and an unknown new card).

2. WHAT IS THE STOCK WORTH TO ME?  E[V | S] = my cards + board + S + the
   hidden board cards drawn from what is left once their hand is set aside.

3. WHAT SHOULD I DO?  Each quote and each trade is chosen by trying a few
   candidates and playing the rest of the deal out in the identified model
   (`rollout`). Against a reader the key lever is our quote: they read it
   as our hand, so a quote just inside their no-trade band moves their
   belief at no cost, and their later quotes then sit on the wrong side
   of the true value. Bigger moves that cost a trade are allowed only once
   the model has been seen to predict a quote correctly. The plan also
   counts both swaps: ours (lowest card away when long, highest when short)
   and theirs (sharp-style bots swap the wrong way for us once they hold
   a position).

Everything is per deal: a fresh Bot() starts from the prior every time.
"""

import math

SMIN, SMAX = 5, 65
GRID = tuple(range(SMIN, SMAX + 1))      # possible opponent hand sums
NG = len(GRID)
LIM = 10                                 # position limit
SQ2 = math.sqrt(2.0)

PUSH_CONF = 0.9    # model mass needed before costly quotes are considered
NQMIN = 1          # ... and at least this many of their quotes seen
NCONF = 1          # reader trust must have predicted this many later quotes
HEDGE = 0.7        # before that, weight on "our quotes really do move them"
GEN_UNI = 0.3      # catch-all model: share of its quote density that is flat
TSOLVE = 2.5       # solve a reader's trust once our quote is this far from neutral
MAXS = 4           # posterior summarised by at most this many points
RESP_M = 1.0       # extra edge wanted per lot when no exact model fits
STAIR = 1.95       # a free nudge: just inside their 2-point no-trade band
TGRID = (0.15, 0.5, 0.85)

# A sharp-style opponent with hand sum S (index S - 5) swaps its lowest card
# when long if it is more than 3 under the average, its highest when short if
# more than 3 over. Expected rise of V when it is long, probability that it
# qualifies, and the mirror images for when it is short.
LO_V = (6.0, 6.0, 6.0, 6.6, 6.6, 6.5, 6.5, 6.5, 6.4, 6.4, 6.3, 6.3, 6.2, 6.2, 6.1, 6.1, 6.0, 5.9, 5.9, 5.8,
        5.7, 5.7, 5.6, 5.5, 5.4, 5.3, 5.2, 5.1, 4.9, 4.8, 4.3, 4.0, 3.8, 3.6, 3.3, 3.0, 2.8, 2.5, 2.3, 2.0,
        1.7, 1.4, 1.2, 1.0, 0.8, 0.6, 0.4, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
LO_P = (1.0,) * 26 + (0.99, 0.99, 0.98, 0.97, 0.83, 0.8, 0.76, 0.72, 0.68, 0.63, 0.59, 0.53, 0.48, 0.42, 0.37,
                      0.32, 0.27, 0.22, 0.17, 0.13, 0.09, 0.05, 0.03, 0.01) + (0.0,) * 11
HI_V = tuple(reversed(LO_V))
HI_P = tuple(reversed(LO_P))

# (name, kind, trust, quote noise, response noise, prior weight, exact)
#   kind R: quotes its fair value (trust None = solved from the data)
#   kind P: quotes the public estimate     kind A: ai_typical style
#   kind X: liar style (mirrors its hand in rounds 1-2)
MODELS = (
    ("rfree", "R", None, 0.03, 0.05, 3.0, 1),
    ("hider", "P", 0.8, 0.03, 0.05, 0.4, 1),
    ("ai", "A", 0.8, 0.03, 0.05, 0.4, 1),
    ("liar", "X", 0.8, 0.03, 0.05, 0.4, 1),
    ("gen", "R", 0.6, 3.0, 3.0, 1.2, 0),
    ("genflat", "P", 0.5, 0.0, 4.0, 0.6, 0),
)
K = len(MODELS)


def phi(x):
    """Standard normal CDF."""
    if x > 7.0:
        return 1.0
    if x < -7.0:
        return 0.0
    return 0.5 * (1.0 + math.erf(x / SQ2))


def public_est(Bs, nb, Ds, nd):
    """Value anyone can work out: board + other cards at the public average."""
    return Bs + (15 - nb) * (364 - Bs - Ds) / (52 - nb - nd)


def their_fair(kind, t, ctx, S, qlast):
    """The opponent's fair value if its hand sums to S (its own view).

    The reader formula from strategies/reader.py with trust t: its unseen
    average m, our hand guessed at 5m and moved t of the way towards what
    our last quote implies. ctx is what the opponent could see at the time.
    """
    rnd, Bs, nb, Ds, nd, npk, pksum, opos, oswapped = ctx
    m = (364 - S - Bs - Ds - pksum) / (52 - 5 - nb - nd - npk)
    hb = 5 - nb
    oh = pksum + (5 - npk) * m
    if qlast is not None:
        implied = qlast - Bs - (5 + hb) * m
        oh += t * (implied - oh)
    f = S + Bs + oh + hb * m
    if kind == "A" and not oswapped and rnd < 5:
        if opos < 0:
            f += 3.9
        elif opos > 0:
            f -= 3.9
    return f


def their_quote(kind, t, ctx, S, qlast):
    """The price the opponent would quote if its hand sums to S."""
    if kind == "P":
        return public_est(ctx[1], ctx[2], ctx[3], ctx[4])
    f = their_fair(kind, t, ctx, S, qlast)
    if kind == "A":
        f += 0.3 * (public_est(ctx[1], ctx[2], ctx[3], ctx[4]) - f)
    elif kind == "X" and ctx[0] <= 2:
        rnd, Bs, nb, Ds, nd, npk, pksum = ctx[:7]
        m = (364 - S - Bs - Ds - pksum) / (52 - 5 - nb - nd - npk)
        f -= 2 * (S - 5 * m)
    return f


def resp_qty(sharp, edge):
    """Lots a taker trades at `edge` = its fair - our price (sharp or all-or-nothing)."""
    if edge > 2:
        return 2 if (not sharp or edge >= 3) else 1
    if edge < -2:
        return -2 if (not sharp or edge <= -3) else -1
    return 0


def resp_prob(edge, qty, lo, hi, sg, psz):
    """P(they traded qty | their edge), with noise sg; psz = P(sharp sizing)."""
    pb = phi((edge - 2) / sg)
    ps = phi((-edge - 2) / sg)
    if qty > 0:
        if qty >= hi:              # all it was allowed: any buy explains it
            return pb
        if qty == 1:               # one lot with room for two: sharp sizing, 2 < edge < 3
            return psz * (pb - phi((edge - 3) / sg))
        return (1 - psz) * pb + psz * phi((edge - 3) / sg)
    if qty < 0:
        if qty <= lo:
            return ps
        if qty == -1:
            return psz * (ps - phi((-edge - 3) / sg))
        return (1 - psz) * ps + psz * phi((-edge - 3) / sg)
    p = 1.0 - pb - ps
    if hi <= 0:
        p += pb
    if lo >= 0:
        p += ps
    return p


def schedule(seat):
    """For quote j = 0..9 of a deal: (round, ours?, first of a round?, our last?, theirs left)."""
    makers = []
    for j in range(10):
        rnd = j // 2 + 1
        first = 0 if rnd % 2 == 1 else 1
        makers.append((first if j % 2 == 0 else 1 - first) == seat)
    last_m = max(j for j in range(10) if makers[j])
    return tuple((j // 2 + 1, makers[j], j % 2 == 0 and j > 0, j == last_m,
                  sum(1 for i in range(j + 1, 10) if not makers[i])) for j in range(10))


SCHED = (schedule(0), schedule(1))


def rollout(ev, j0, Q, pos, d, p, my_long, my_short, pns, fl_long, fl_short):
    """Play quotes j0..9 against one fixed opponent hypothesis; PnL vs E[V].

    Simple policy: take their quote whenever it pays. As maker, nudge their
    belief one stair in direction d (+1: make them think the stock is cheap,
    so we can buy) without trading, except on our last quote or when their
    quotes alone cannot fill the position, when we trade at the best price
    their response allows. Their swap (sharp-style) happens at a round start
    once they hold a position; ours is booked at the end.
    """
    Vb, af, tf, fnone, aq, bq, qnone, sz, akind, lo_v, lo_p, hi_v, hi_p, mg = p
    pnl = 0.0
    kk = 3.05 if sz else 2.05
    for j in range(j0, 10):
        rnd, mine, newround, last_m, t_left = ev[j]
        if newround and pns > 0.02:
            if pos < 0 and not fl_long:          # they are long: V rises
                pnl += pos * pns * lo_v
                pns *= 1.0 - lo_p
                fl_long = True
            elif pos > 0 and not fl_short:       # they are short: V falls
                pnl -= pos * pns * hi_v
                pns *= 1.0 - hi_p
                fl_short = True
        if not mine:
            price = qnone if Q is None else aq + bq * Q
            g = Vb - price - 2.0
            if g > 0 and pos < LIM:
                n = 2 if pos <= LIM - 2 else LIM - pos
                pos += n
                pnl += n * g
            else:
                g = price - 2.0 - Vb
                if g > 0 and pos > -LIM:
                    n = 2 if pos >= 2 - LIM else LIM + pos
                    pos -= n
                    pnl += n * g
        else:
            # their edge on our quote x is c0 + c1 * x
            if akind:
                c0, c1 = af, tf - 1.0
            else:
                c0, c1 = (fnone if Q is None else af + tf * Q), -1.0
            cap = LIM - pos if d > 0 else LIM + pos
            done = False
            if last_m or cap > 2 * t_left:
                xb = (-kk - c0) / c1             # they sell us 2 at xb - 2
                gb = Vb - xb + 2.0
                xs = (kk - c0) / c1              # they buy 2 from us at xs + 2
                gs = xs + 2.0 - Vb
                if gb > 0 and gb >= gs and pos < LIM:
                    n = 2 if pos <= LIM - 2 else LIM - pos
                    pos += n
                    pnl += n * gb
                    Q = xb
                    done = True
                elif gs > 0 and pos > -LIM:
                    n = 2 if pos >= 2 - LIM else LIM + pos
                    pos -= n
                    pnl += n * gs
                    Q = xs
                    done = True
            if not done:
                Q = (mg * d - c0) / c1
    if pos > 0:
        pnl += pos * my_long
    elif pos < 0:
        pnl -= pos * my_short
    return pnl


class Bot:
    def __init__(self):
        self.J = None                  # J[k][i]: weight of (model k, S = GRID[i])
        self.prior = None
        self.T = [None] * NG           # rfree: trust solved for each hand sum
        self.alive = [True] * K
        self.done_tape = set()
        self.n_disc = 0
        self.pending = {}              # our quotes awaiting their response
        self.seat = None
        self.start_pos = {}
        self.fl_long = False           # seen holding long without swapping
        self.fl_short = False
        self.checked = set()
        self.psz = 0.6                 # P(opponent sizes trades like sharp)
        self.top_mass = 0.0
        self.top_k = 0
        self.confirm = 0               # later quotes the solved trust predicted
        self.conf_q = None
        self.nq = 0                    # their quotes seen

    # ------------------------------------------------------------ inference
    def _init(self, obs):
        """Prior on S: five cards from what we cannot see (normal approximation)."""
        un = obs.unseen
        N = sum(un)
        mu = sum((r + 1) * c for r, c in enumerate(un)) / N
        var = sum((r + 1 - mu) ** 2 * c for r, c in enumerate(un)) / N
        v5 = 5 * var * (N - 5) / (N - 1)
        prior = [math.exp(-0.5 * (s - 5 * mu) ** 2 / v5) for s in GRID]
        z = sum(prior)
        self.prior = [p / z for p in prior]
        self.J = [[p * mdl[5] for p in self.prior] for mdl in MODELS]

    def _ctx(self, obs):
        """What the opponent could see when acting now."""
        npk = min(5, sum(1 for _, w in obs.peeks if w == "opp"))
        pksum = npk * sum(obs.hand) / 5.0
        oswapped = any(w == "opp" for _, w, _ in obs.discards)
        return (obs.round, sum(obs.board), len(obs.board),
                sum(r for _, _, r in obs.discards), len(obs.discards),
                npk, pksum, -obs.position, oswapped)

    def _normalize(self):
        J = self.J
        mx = 0.0
        for k in range(K):
            if self.alive[k]:
                v = max(J[k])
                if v > mx:
                    mx = v
        if mx <= 0:
            # nothing explains what we saw: start again from the prior
            self.alive = [True] * K
            self.T = [None] * NG
            self.J = [[p * mdl[5] for p in self.prior] for mdl in MODELS]
            return
        inv = 1.0 / mx
        for k in range(K):
            if self.alive[k]:
                row = J[k]
                big = 0.0
                for i in range(NG):
                    v = row[i] * inv
                    if v < 1e-12:
                        v = 0.0
                    row[i] = v
                    if v > big:
                        big = v
                if big < 1e-9:
                    self.alive[k] = False

    def _obs_quote(self, ctx, qlast, price):
        """Their quote `price`, made when our last quote was qlast."""
        J = self.J
        r0 = J[0]
        m0 = sum(r0)
        known = sum(r0[i] for i in range(NG) if self.T[i] is not None)
        test = (self.alive[0] and m0 > 0 and known > 0.9 * m0 and qlast is not None
                and (self.conf_q is None or abs(qlast - self.conf_q) >= 1.0))
        for k in range(K):
            if not self.alive[k]:
                continue
            name, kind, t, sg, _, _, exact = MODELS[k]
            row = J[k]
            if sg <= 0:
                for i in range(NG):
                    row[i] *= 0.03             # quotes carry no information
                continue
            if t is None:
                # reader family, trust unknown: quote = A(S) + t * D(S)
                a0 = their_quote(kind, 0.0, ctx, 0, qlast)
                a1 = their_quote(kind, 0.0, ctx, 1, qlast) - a0
                d0 = their_quote(kind, 1.0, ctx, 0, qlast) - a0
                d1 = their_quote(kind, 1.0, ctx, 1, qlast) - a0 - a1 - d0
                T = self.T
                for i in range(NG):
                    if not row[i]:
                        continue
                    S = GRID[i]
                    A = a0 + a1 * S
                    D = d0 + d1 * S
                    ts = T[i]
                    if ts is not None:
                        sgx = sg + 0.004 * abs(D)
                        dd = (price - A - ts * D) / sgx
                        e = -0.5 * dd * dd
                        row[i] *= (math.exp(e) / sgx if e > -60 else 0.0) + 1e-6
                    elif abs(D) >= TSOLVE:
                        tt = (price - A) / D
                        if -0.03 <= tt <= 1.03:
                            row[i] *= 1.0 / abs(D)
                            T[i] = min(1.0, max(0.0, tt))
                        else:
                            row[i] *= 1e-6
                    elif abs(D) < 0.05:
                        dd = (price - A) / sg
                        e = -0.5 * dd * dd
                        row[i] *= (math.exp(e) / sg if e > -60 else 0.0) + 1e-6
                    else:
                        # trust uniform on [0, 1]: the quote is in a box of width |D|
                        lo_v = A if D > 0 else A + D
                        row[i] *= (phi((price - lo_v) / sg) - phi((price - lo_v - abs(D)) / sg)) / abs(D) + 1e-6
                continue
            a = their_quote(kind, t, ctx, 0, qlast)
            b = their_quote(kind, t, ctx, 1, qlast) - a
            c = -0.5 / (sg * sg)
            inv = 1.0 / sg
            if not exact:
                # catch-all: heavy tails, so one odd quote cannot dominate
                u = GEN_UNI / 40.0
                inv *= 1.0 - GEN_UNI
                for i in range(NG):
                    if row[i]:
                        d = price - a - b * GRID[i]
                        e = c * d * d
                        row[i] *= inv * (math.exp(e) if e > -60 else 0.0) + u
                continue
            if b == 0.0:
                d = price - a
                e = c * d * d
                w = inv * (math.exp(e) if e > -60 else 0.0) + 1e-6
                for i in range(NG):
                    row[i] *= w
            else:
                for i in range(NG):
                    if row[i]:
                        d = price - a - b * GRID[i]
                        e = c * d * d
                        row[i] *= inv * (math.exp(e) if e > -60 else 0.0) + 1e-6
        self._normalize()
        J = self.J
        if test and self.alive[0]:
            tot = sum(sum(J[k]) for k in range(K) if self.alive[k])
            if sum(J[0]) > 0.9 * tot:
                self.confirm += 1
        if qlast is not None and self.alive[0]:
            r0 = J[0]
            if sum(r0[i] for i in range(NG) if self.T[i] is not None) > 0.9 * sum(r0):
                self.conf_q = qlast

    def _obs_resp(self, ctx, qlast, price, qty, mypos):
        """They traded qty on our quote `price` (their last view of us: qlast)."""
        lo = max(-2, mypos - LIM)
        hi = min(2, mypos + LIM)
        J = self.J
        psz = self.psz
        sz_ev = [0.0, 0.0]
        for k in range(K):
            if not self.alive[k]:
                continue
            name, kind, t, _, sg, _, exact = MODELS[k]
            ql = price if kind == "A" else qlast
            row = J[k]
            if t is None:
                a0 = their_fair(kind, 0.0, ctx, 0, ql)
                a1 = their_fair(kind, 0.0, ctx, 1, ql) - a0
                d0 = their_fair(kind, 1.0, ctx, 0, ql) - a0
                d1 = their_fair(kind, 1.0, ctx, 1, ql) - a0 - a1 - d0
                T = self.T
                for i in range(NG):
                    w = row[i]
                    if not w:
                        continue
                    S = GRID[i]
                    A = a0 + a1 * S
                    D = d0 + d1 * S
                    ts = T[i]
                    if ts is not None:
                        edge = A + ts * D - price
                        p = resp_prob(edge, qty, lo, hi, sg, psz)
                        if 2.05 < abs(edge) < 2.95 and qty:
                            room = hi if qty > 0 else -lo
                            if room >= 2:      # one lot or two tells us their sizing
                                sz_ev[0 if abs(qty) == 1 else 1] += w
                    else:
                        p = 0.0
                        for tt in TGRID:
                            p += resp_prob(A + tt * D - price, qty, lo, hi, sg + 0.05 * abs(D), psz)
                        p /= len(TGRID)
                    row[i] = w * (p + 1e-4)
                continue
            a = their_fair(kind, t, ctx, 0, ql)
            b = their_fair(kind, t, ctx, 1, ql) - a
            for i in range(NG):
                w = row[i]
                if w:
                    row[i] = w * (resp_prob(a + b * GRID[i] - price, qty, lo, hi, sg, psz) + 1e-4)
        tot = sz_ev[0] + sz_ev[1]
        if tot > 0:
            f1 = sz_ev[0] / tot
            pl = psz * (0.05 + 0.95 * f1)
            pa = (1 - psz) * (0.05 + 0.95 * (1 - f1))
            self.psz = pl / (pl + pa)
        self._normalize()

    def _obs_swap(self, obs, rd):
        """They swapped away rank rd: S becomes S - rd + (a card we cannot see)."""
        un = obs.unseen
        N = sum(un)
        px = [(x + 1, c / N) for x, c in enumerate(un) if c]
        J = self.J
        for k in range(K):
            if not self.alive[k]:
                continue
            row = J[k]
            new = [0.0] * NG
            free = MODELS[k][2] is None
            T = self.T
            tw = [0.0] * NG
            tn = [0.0] * NG
            for i in range(NG):
                w = row[i]
                if not w:
                    continue
                base = GRID[i] - rd - SMIN
                ts = T[i] if free else None
                for x, p in px:
                    s = base + x
                    if 0 <= s < NG:
                        v = w * p
                        new[s] += v
                        if ts is not None:
                            tw[s] += v * ts
                            tn[s] += v
            J[k] = new
            if free:
                self.T = [tw[i] / tn[i] if tn[i] > 0 and tn[i] > 0.5 * new[i] else None
                          for i in range(NG)]
        self._normalize()

    def _sync(self, obs):
        """Fold in everything new on the tape and in the discards, in order."""
        if self.J is None:
            self._init(obs)
        tape = obs.tape
        if self.seat is None and tape:
            self.seat = 0 if tape[0][1] == "me" else 1
        disc = obs.discards
        events = []
        for j in range(self.n_disc, len(disc)):
            r, w, rk = disc[j]
            if w == "opp":
                events.append((r, 0, j, rk))
        self.n_disc = len(disc)
        for j in range(len(tape)):
            if j in self.done_tape:
                continue
            self.done_tape.add(j)
            r, w, px, q = tape[j]
            if w == "me" and j in self.pending:
                events.append((r, 1, j, (px, q)))
        events.sort()
        for r, typ, j, data in events:
            if typ == 0:
                self._obs_swap(obs, data)
            else:
                ctx, qlast, mypos = self.pending.pop(j)
                self._obs_resp(ctx, qlast, data[0], data[1], mypos)

    # ------------------------------------------------------------ estimates
    def _ev_lin(self, obs):
        """E[V | S] = c0 + c1 * S (hidden board drawn from what their hand leaves)."""
        un = obs.unseen
        U = sum((r + 1) * c for r, c in enumerate(un))
        N = sum(un)
        ok = obs.opp_known
        hb = 5 - len(obs.board)
        den = N - 5 + len(ok)
        return (sum(obs.hand) + sum(obs.board) + hb * (U + sum(ok)) / den,
                1.0 - hb / den)

    def _samples(self):
        """At most MAXS (weight, model, S, trust) points summarising the posterior."""
        J = self.J
        masses = []
        tot = 0.0
        for k in range(K):
            if self.alive[k]:
                s = sum(J[k])
                masses.append((s, k))
                tot += s
        masses.sort(reverse=True)
        self.top_mass = masses[0][0] / tot
        self.top_k = masses[0][1]
        out = []
        T = self.T
        for s, k in masses:
            w = s / tot
            if w < 0.03 and out:
                break
            row = J[k]
            mu = sum(p * g for p, g in zip(row, GRID)) / s
            var = sum(p * (g - mu) ** 2 for p, g in zip(row, GRID)) / s
            sd = math.sqrt(max(var, 0.0))
            t = MODELS[k][2]
            if t is None:
                tw = 0.0
                tn = 0.0
                for i in range(NG):
                    if row[i] and T[i] is not None:
                        tw += row[i] * T[i]
                        tn += row[i]
                t = tw / tn if tn > 0.5 * s else 0.6
            if sd < 1.5:
                out.append((w, k, mu, t))
            else:                       # 3-point Gauss-Hermite in S
                h = 1.732 * sd
                out.append((w * 0.6667, k, mu, t))
                out.append((w * 0.1667, k, mu - h, t))
                out.append((w * 0.1667, k, mu + h, t))
        out.sort(reverse=True)
        out = out[:MAXS]
        z = sum(o[0] for o in out)
        return [(w / z, k, s, t) for w, k, s, t in out]

    def _t_known(self):
        """Is the main hypothesis' trust pinned down?"""
        if MODELS[self.top_k][2] is not None:
            return True
        row = self.J[self.top_k]
        tn = sum(row[i] for i in range(NG) if self.T[i] is not None)
        return tn > 0.95 * sum(row)

    def _params(self, ctx, k, S, t, c0, c1, mg):
        """Linearised opponent hypothesis for `rollout`."""
        kind = MODELS[k][1]
        fnone = their_fair(kind, t, ctx, S, None)
        af = their_fair(kind, t, ctx, S, 0.0)
        tf = (their_fair(kind, t, ctx, S, 100.0) - af) / 100.0
        qnone = their_quote(kind, t, ctx, S, None)
        aq = their_quote(kind, t, ctx, S, 0.0)
        bq = (their_quote(kind, t, ctx, S, 100.0) - aq) / 100.0
        i = min(NG - 1, max(0, int(round(S)) - SMIN))
        return (c0 + c1 * S, af, tf, fnone, aq, bq, qnone, self.psz > 0.5, kind == "A",
                LO_V[i], LO_P[i], HI_V[i], HI_P[i], mg)

    def _hyps(self, ctx, samples, c0, c1):
        return [(w, self._params(ctx, k, s, t, c0, c1, STAIR if MODELS[k][6] else 0.0))
                for w, k, s, t in samples]

    def _my_gains(self, obs):
        """Swap gain per lot still available: long (lowest card) and short (highest)."""
        if any(w == "me" for _, w, _ in obs.discards):
            return 0.0, 0.0
        un = obs.unseen
        m = sum((r + 1) * c for r, c in enumerate(un)) / sum(un)
        return max(0.0, m - min(obs.hand)), max(0.0, max(obs.hand) - m)

    def _opp_state(self, obs):
        if any(w == "opp" for _, w, _ in obs.discards):
            return 0.0, True, True
        return 1.0, self.fl_long, self.fl_short

    @staticmethod
    def _last_me(tape):
        for r, w, px, q in reversed(tape):
            if w == "me":
                return px
        return None

    # ------------------------------------------------------------ actions
    def move(self, obs):
        try:
            return self._move(obs)
        except Exception:
            return None

    def quote(self, obs):
        try:
            return self._quote(obs)
        except Exception:
            un = obs.unseen
            return round(sum(obs.hand) + sum(obs.board)
                         + (10 - len(obs.board)) * sum((r + 1) * c for r, c in enumerate(un)) / sum(un), 2)

    def respond(self, obs, price):
        try:
            return self._respond(obs, price)
        except Exception:
            return 0

    def _move(self, obs):
        self._sync(obs)
        rnd = obs.round
        self.start_pos[rnd] = obs.position
        # they held a position at the last round start and did not swap: their
        # card in that direction does not qualify, so no swap that way later
        r0 = rnd - 1
        if r0 >= 2 and r0 not in self.checked:
            self.checked.add(r0)
            p0 = self.start_pos.get(r0, 0)
            if not any(w == "opp" for _, w, _ in obs.discards):
                if p0 < 0:
                    self.fl_long = True
                elif p0 > 0:
                    self.fl_short = True
        if any(w == "me" for _, w, _ in obs.discards):
            return None                       # our one swap is spent
        pos = obs.position
        if pos == 0:
            return None
        un = obs.unseen
        m = sum((r + 1) * c for r, c in enumerate(un)) / sum(un)
        hand = obs.hand
        if pos > 0:                           # long: every point added is ours
            i = min(range(5), key=lambda j: hand[j])
            gain = pos * (m - hand[i])
        else:
            i = max(range(5), key=lambda j: hand[j])
            gain = -pos * (hand[i] - m)
        if (rnd == 5 and gain > 0) or (rnd >= 3 and abs(pos) >= 6 and gain > 6):
            return ("SWAP", i)
        return None

    def _quote(self, obs):
        self._sync(obs)
        if self.seat is None:
            self.seat = 0
        ctx = self._ctx(obs)
        qlast = self._last_me(obs.tape)
        if not obs.tape:
            # first quote of the deal, nothing known yet: the public estimate
            # gives our hand away to nobody and keeps their reply easy to read
            un = obs.unseen
            m = sum((r + 1) * c for r, c in enumerate(un)) / sum(un)
            self.pending[0] = (ctx, qlast, obs.position)
            return round(15 * m, 2)
        c0, c1 = self._ev_lin(obs)
        samples = self._samples()
        ev = sum(w * (c0 + c1 * s) for w, k, s, t in samples)
        pos = obs.position
        lo = max(-2, pos - LIM)
        hi = min(2, pos + LIM)
        j = len(obs.tape)
        sched = SCHED[self.seat]
        mg_l, mg_s = self._my_gains(obs)
        pns, fl_l, fl_s = self._opp_state(obs)
        P = self._hyps(ctx, samples, c0, c1)
        # their edge on our quote x is e0 + e1 * x under the main hypothesis
        p0 = max(P, key=lambda x: x[0])[1]
        sure = self.top_mass >= PUSH_CONF and self.nq >= NQMIN
        if p0[8] and sure:
            e0, e1 = p0[1], p0[2] - 1.0
        elif p0[8]:
            e0, e1 = p0[1] + p0[2] * (qlast if qlast is not None else ev), -1.0
        else:
            e0, e1 = (p0[3] if qlast is None else p0[1] + p0[2] * qlast), -1.0
        exact = MODELS[self.top_k][6]
        if exact:
            edges = [STAIR, -STAIR, 2.05, -2.05, 2.5, -2.5, 3.05, -3.05]
            cands = [ev]
        else:
            edges = [2.05, -2.05, 3.05, -3.05]
            cands = [ev + d for d in (-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5)]
        confident = (sure and exact and self._t_known()
                     and (self.top_k != 0 or self.confirm >= NCONF))
        if not confident and HEDGE > 0 and self.top_k == 0 and sure and self._t_known():
            # trust fitted but not yet seen to predict a later quote: allow big
            # quotes, but price in the chance that our quotes do not move them
            s0 = next((s_ for w, k, s_, t in samples if k == 0), None)
            if s0 is not None:
                P = [(w * HEDGE, p) for w, p in P] + [
                    (1.0 - HEDGE, self._params(ctx, 0, s0, 0.0, c0, c1, STAIR))]
                confident = True
        if confident:
            edges += [6.0, -6.0, 9.0, -9.0, 13.0, -13.0]
            cands += [ev - 2, ev + 2, ev - 4, ev + 4]
        for edge in edges:
            cands.append((edge - e0) / e1)
        best, bq = -1e18, ev
        seen = set()
        fm = e0 if e1 == -1.0 else ev
        for x in cands:
            x = round(x, 2)
            key = round(x * 10)
            if key in seen or (not confident and abs(x - ev) > 12.0 and abs(x - fm) > 4.0):
                continue
            seen.add(key)
            vals = [0.0, 0.0]
            for w, p in P:
                if p[8]:
                    edge = p[1] + p[2] * x - x
                else:
                    edge = (p[3] if qlast is None else p[1] + p[2] * qlast) - x
                n = max(lo, min(hi, resp_qty(p[7], edge)))
                imm = 0.0
                if n > 0:
                    imm = n * (x + 2 - p[0])
                elif n < 0:
                    imm = -n * (p[0] - x + 2)
                np_ = pos - n
                for di, d in enumerate((1, -1)):
                    vals[di] += w * (imm + rollout(sched, j + 1, x, np_, d, p, mg_l, mg_s, pns, fl_l, fl_s))
            v = max(vals)
            if v > best:
                best, bq = v, x
        bq = min(195.0, max(0.0, round(bq, 2)))
        self.pending[j] = (ctx, qlast, pos)
        return bq

    def _respond(self, obs, price):
        self._sync(obs)
        if self.seat is None:
            self.seat = 1
        ctx = self._ctx(obs)
        qlast = self._last_me(obs.tape)
        self._obs_quote(ctx, qlast, price)     # their quote is news: read it first
        self.nq += 1
        j = len(obs.tape)
        self.done_tape.add(j)
        c0, c1 = self._ev_lin(obs)
        samples = self._samples()
        pos = obs.position
        sched = SCHED[self.seat]
        mg_l, mg_s = self._my_gains(obs)
        pns, fl_l, fl_s = self._opp_state(obs)
        P = self._hyps(ctx, samples, c0, c1)
        margin = 0.0 if MODELS[self.top_k][6] else RESP_M
        best, bn = -1e18, 0
        for n in (0, 2, -2, 1, -1):
            if pos + n > LIM or pos + n < -LIM:
                continue
            vals = [0.0, 0.0]
            for w, p in P:
                imm = n * (p[0] - price - 2) if n > 0 else -n * (price - 2 - p[0])
                imm -= abs(n) * margin
                for di, d in enumerate((1, -1)):
                    vals[di] += w * (imm + rollout(sched, j + 1, qlast, pos + n, d, p, mg_l, mg_s, pns, fl_l, fl_s))
            v = max(vals)
            if v > best + 1e-9:
                best, bn = v, n
        return bn
