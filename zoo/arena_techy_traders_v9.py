# Team Name: Zoo - arena_techy_traders_v9
# Members: Organisers
# Mentor: None

"""
arena_techy_traders_v9.py - imitation of arena team "Techy Traders" v9 (entry #416), decoded
from its public replays (zoo/arena_raw/techy_traders/, 58 fights). Live: 53 wins in 58 fights,
mean +6.49; house reader +28.43, house sharp +26.79, house naive +10.57; lost only to Alpha Rodeo
#393 (hunt_v02, -1.26), Imposters (-0.93), PaperHands (-0.32), Cyberpsycho (-0.10), TeenPatti (-0.06).

What the replays show, and what this file does:
  * First quote: the public estimate + 2.94 (107.94 at the start).
  * It identifies the opponent's model and hand exactly (here: rival_3's inference). Against
    naive its quotes sit at naive's exact fair +-2.01 when it wants a trade, +-1.0 / 0.0 when not.
  * READER CRUSHER: once the opponent is known to read quotes (trust pinned down), it quotes
    0.00 once (rounds <= 3), whatever its own position. The reader buys 2 at 2.00 (a ~220 loss),
    reads the quote as a tiny hand, and its value collapses (house reader 113 -> 49 -> 71).
    From then on it quotes the reader's fair + 3.01, so the reader keeps SELLING to it far below
    the real value; it also buys the reader's collapsed quotes as taker.
  * Opponents it cannot identify: their last quote stands in for their fair, same rules.
  * No trade wanted: quotes 0.97 past their fair AGAINST its own side (bullish -> below).
    At the position limit: their exact fair.
  * Taker on its value with a margin and an inventory skew; swaps in round 5 when holding a
    position (lowest card if long, highest if short). Never peeks.

Fidelity (8 Oct, 3 x 400 deals, seeds 1 2): house naive +10.17 (live +10.57), reader +23.26
(live +28.43), sharp +21.00 (live +26.79), vs versions/hunt_v02.py -3.05 (live vs #393 -1.26).
Swaps 578/580 decisions; quotes after the crush within 0.1 of the real ones. Known gap: the real
bot starts the crush earlier (round 2 vs sharp, before the reading trust is pinned down), which is
why it farms readers harder; an earlier trigger made this copy crush naive too (-11), so it waits.
"""

import math

SMIN, SMAX = 5, 65
GRID = tuple(range(SMIN, SMAX + 1))      # possible opponent hand sums
NG = len(GRID)
LIM = 10                                 # position limit
SQ2 = math.sqrt(2.0)
GEN_UNI = 0.3
TSOLVE = 2.5
MAXS = 4
TGRID = (0.15, 0.5, 0.85)

# decoded PaperHands policy
EDGE = 2.01
EDGE_MIN = 2.3
NEUTRAL = 0.97
PUSH = 13.0
PUSH_K = 0.9
PUSH_TMIN = 0.3
ID_CONF = 0.9
TAKE_M = 1.0
TAKE_M2 = 2.0
TAKE_POS = 0.3
U_TEV = 2.2
U_TRUST = 0.0
R1_ADD = 2.94
AFTER = 3.01
ZERO_RMAX = 3
PUSH_STRICT = 1.0

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

    @staticmethod
    def _last_me(tape):
        for r, w, px, q in reversed(tape):
            if w == "me":
                return px
        return None

    # ------------------------------------------------------------ PaperHands policy
    def move(self, obs):
        try:
            self._sync(obs)
            if obs.round != 5 or obs.position == 0:
                return None
            if any(w == "me" for _, w, _ in obs.discards):
                return None
            un = obs.unseen
            m = sum((r + 1) * c for r, c in enumerate(un)) / sum(un)
            h = obs.hand
            if obs.position > 0:
                i = min(range(5), key=lambda j: h[j])
                return ("SWAP", i) if h[i] < m else None
            i = max(range(5), key=lambda j: h[j])
            return ("SWAP", i) if h[i] > m else None
        except Exception:
            return None

    def quote(self, obs):
        try:
            return self._quote(obs)
        except Exception:
            return round(self._public(obs), 2)

    def respond(self, obs, price):
        try:
            return self._respond(obs, price)
        except Exception:
            return 0

    @staticmethod
    def _public(obs):
        return public_est(sum(obs.board), len(obs.board),
                          sum(r for _, _, r in obs.discards), len(obs.discards))

    def _view(self, obs, ctx, qlast):
        """(my EV, predicted opponent fair when it answers, identified?, reader trust)."""
        c0, c1 = self._ev_lin(obs)
        samples = self._samples()
        ev = sum(w * (c0 + c1 * s) for w, k, s, t in samples)
        P = 0.0
        for w, k, s, t in samples:
            P += w * their_fair(MODELS[k][1], t, ctx, s, qlast)
        top = max(samples, key=lambda x: x[0])
        ident = MODELS[self.top_k][6] == 1 and self.top_mass >= ID_CONF
        trust = top[3] if MODELS[top[1]][1] == "R" and (self._t_known() or not PUSH_STRICT) else 0.0
        return ev, P, ident, trust

    def _t_known(self):
        """Is the main hypothesis' reading trust pinned down by the data?"""
        if MODELS[self.top_k][2] is not None:
            return True
        row = self.J[self.top_k]
        tn = sum(row[i] for i in range(NG) if self.T[i] is not None)
        return tn > 0.95 * sum(row)

    def _value(self, obs, price=None):
        """My value. Identified opponent: the posterior EV. Otherwise their
        quotes are not believed: naive value + U_TRUST x what their latest
        quote implies + U_TEV per lot they bought from my quotes (- per lot sold)."""
        c0, c1 = self._ev_lin(obs)
        samples = self._samples()
        if MODELS[self.top_k][6] == 1 and self.top_mass >= ID_CONF:
            return sum(w * (c0 + c1 * s) for w, k, s, t in samples)
        un = obs.unseen
        m = sum((r + 1) * c for r, c in enumerate(un)) / sum(un)
        hb = 5 - len(obs.board)
        v = sum(obs.hand) + sum(obs.board) + (5 + hb) * m
        theirs = [px for r, w, px, q in obs.tape if w == "opp"]
        if price is not None:
            theirs.append(price)
        if theirs and U_TRUST:
            v += U_TRUST * (theirs[-1] - sum(obs.board) - (10 + hb) * m)
        v += U_TEV * sum(q for r, w, px, q in obs.tape if w == "me")
        return v

    def _quote(self, obs):
        self._sync(obs)
        if self.seat is None:
            self.seat = 0
        ctx = self._ctx(obs)
        qlast = self._last_me(obs.tape)
        j = len(obs.tape)
        self.pending[j] = (ctx, qlast, obs.position)
        theirs = [px for r, w, px, q in obs.tape if w == "opp"]
        if not theirs:
            return round(self._public(obs) + R1_ADD, 2)
        ev, P, ident, trust = self._view(obs, ctx, qlast)
        if not ident:
            P = theirs[-1]                               # unknown type: their quote is their fair
            trust = 0.0
        ev = self._value(obs)
        pos = obs.position
        gap = ev - P
        room_buy = pos < LIM
        room_sell = pos > -LIM
        pushed = getattr(self, "pushed", False)
        if trust >= PUSH_TMIN and not pushed and obs.round <= ZERO_RMAX and room_sell:
            self.pushed = True
            return 0.0                                   # crush the reader's belief
        if pushed and trust >= PUSH_TMIN and room_buy:
            return round(P + AFTER, 2)                   # they keep selling to us cheap
        if (gap > 0 and not room_buy) or (gap < 0 and not room_sell):
            return round(P, 2)                           # at the limit: no trade
        if gap > EDGE_MIN:
            return round(P + EDGE, 2)                    # they sell to us at P + 0.01
        if gap < -EDGE_MIN:
            return round(P - EDGE, 2)                    # they buy from us at P - 0.01
        return round(P - (NEUTRAL if gap > 0 else -NEUTRAL), 2)   # no trade, nudged against our side

    def _respond(self, obs, price):
        self._sync(obs)
        if self.seat is None:
            self.seat = 1
        ctx = self._ctx(obs)
        qlast = self._last_me(obs.tape)
        self._obs_quote(ctx, qlast, price)
        self.nq += 1
        self.done_tape.add(len(obs.tape))
        e = self._value(obs, price) - price - TAKE_POS * obs.position
        if e > 2 + TAKE_M2:
            return 2
        if e > 2 + TAKE_M:
            return 1
        if e < -2 - TAKE_M2:
            return -2
        if e < -2 - TAKE_M:
            return -1
        return 0
