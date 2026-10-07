# Team Name: Rival 1
# Members: AI
# Mentor: None

"""
rival_1.py - identify the opponent's pricing rule exactly, then steer it.

1. IDENTIFY. naive, reader, sharp and most of their copies quote
       F = their hand + board + (their estimate of my hand) + hidden board x avg,
   where their estimate of my hand moves a fraction t ("trust") of the way
   towards what my last quote implies (naive is t = 0, reader/sharp t = 0.8).
   F is linear in their hand sum S, so every quote can be inverted for S. For
   each t on a grid (and, if they peeked, each possible card they saw) I keep
   the hypotheses whose S comes out a whole number and stays consistent
   between quotes (allowing for their visible swap). Usually one survives
   after a quote or two, and then I know their hand sum EXACTLY.

2. EXPLOIT (exact mode). Knowing S I know V up to the hidden board, and I know
   their F as a function of my last quote: F = c + t * P_last. A planner
   enumerates my remaining maker turns as "steer" (quote just inside their
   no-trade band, F -/+ 1.97, which drags their belief away from the truth
   without trading) or "harvest" (quote just outside it so they trade 2 lots
   with me at about their F), in both directions, and fills the 10-lot limit
   with the best mix of harvests and taker trades on their quotes. Against
   t = 0 opponents steering does nothing, so it harvests; it also probes
   whether they trade 2 lots inside the 2..3 edge zone so it can harvest
   closer to their fair.

3. FALLBACK (opponent not identified). A Gaussian filter over S, mixing "they
   quote honestly with trust 0, 0.5 or 0.8" with "their quotes are
   uninformative", and also learning from how they answer my quotes. I quote
   relative to my estimate of THEIR fair (so my quote says little about my
   hand), offset to maximise expected profit under the remaining uncertainty,
   and take only with a margin. I never peek: against hand-hiding opponents it
   cost more than the card was worth.

4. SWAP. Against opponents that read my quotes, swap the low card once long
   (high card once short). Against t = 0 opponents, swap whichever extreme
   card makes my edge biggest.

Standard library only; well under 2 ms per call.
"""

import math

# ── exact identification ───────────────────────────────────────────────
TGRID = (0.8, 0.0, 0.5, 0.6, 0.7, 0.9, 1.0, 0.4, 0.3, 0.2, 0.1)   # trust values tried
TPRI = {0.8: 20.0, 0.0: 8.0}    # prior weight of a trust value (others 1)
TOL = 0.0075                    # quotes are rounded to 0.01: allowed misfit in price units
MAX_HYPS = 400

# ── exact-mode trading ─────────────────────────────────────────────────
BAND = 1.97                     # steer quote: this far inside their no-trade band

# ── fallback model ─────────────────────────────────────────────────────
FB_TAKE = 1.5                   # extra edge needed to take their quote
FB_SQ = 2.5                     # quote noise of an "honest" opponent
FB_PH = 0.6                     # prior that they quote honestly
FB_SR = 2.0                     # noise in their buy/sell decisions
FB_SM = 1.0                     # extra uncertainty on their fair
STEER_FB = 0.5                  # shade quotes against my direction (scaled by their trust)

# ── swaps ──────────────────────────────────────────────────────────────
SWAP_MIN = 1.0                  # min gain (vs average unseen card) for a swap
SWAP_D0 = 3.0                   # vs t = 0: min |edge| to commit a swap direction

SQ2 = math.sqrt(2.0)


def Phi(x):
    return 0.5 * (1.0 + math.erf(x / SQ2))


def phi(x):
    return 0.3989422804014327 * math.exp(-0.5 * x * x)


def coef(t, shown, B, dsum, nd, plast, pkh, nkh):
    """Reader-family opponent with trust t: its fair value is a + b * S.

    shown/B: board cards up and their sum; dsum/nd: discards (both players);
    plast: my last quote before theirs (None if I have not quoted);
    pkh/nkh: sum/count of my cards they peeked and I still hold.
    """
    hb = 5 - shown
    N = 47 - shown - nd - nkh             # cards they have not seen
    m0 = (364.0 - B - dsum - pkh) / N     # their average unseen rank is m0 - S / N
    if plast is None:
        t = 0.0
        plast = 0.0
    K = (1 - t) * (5 - nkh) - t * (5 + hb) + hb
    return (1 - t) * (B + pkh) + t * plast + K * m0, 1.0 - K / N


class Bot:
    def __init__(self):
        self.seat = None        # 0: I quote first in odd rounds, 1: in even rounds
        self.h0 = None          # my initial hand
        self.sw = None          # (round, slot) of my swap
        self.newcard = 0        # the card my swap drew
        # hypothesis = (trust, my cards they peeked, their hand sum, their pending discard)
        self.hyps = [(t, (), None, 0) for t in TGRID]
        self.dead = False       # no exact hypothesis fits: fallback for the rest of the deal
        self.done = 0           # tape entries processed
        self.mv_done = 0        # rounds whose move events were processed
        self.ev = []            # chronological events, for the fallback filter
        self.resp = []          # their answers to my quotes
        self.t_eff = 0.8        # fallback: inferred trust
        self.rm = (99.0, 0.0)
        self.full = False
        self.one = False

    # ==================================================================
    #  bookkeeping: replay the public history once, incrementally
    # ==================================================================
    def _rank(self, cid):
        slot, ep = cid
        return self.h0[slot] if ep == 0 else self.newcard

    def _held(self, cid, r):
        """Do I still hold card cid during round r?"""
        if self.sw is None or cid[0] != self.sw[1]:
            return True
        rs = self.sw[0]
        return (cid[1] == 0 and r < rs) or (cid[1] == 1 and r >= rs)

    def _view(self, obs, r, upto):
        """What the opponent saw at tape index `upto` of round r."""
        shown = r - 1
        B = sum(obs.board[:shown])
        dsum = 0
        nd = 0
        for rr, w, c in obs.discards:
            if rr <= r:
                dsum += c
                nd += 1
        plast = None
        tape = obs.tape
        for j in range(upto):
            if tape[j][1] == "me":
                plast = tape[j][2]
        return shown, B, dsum, nd, plast

    def _sync(self, obs, extra=None, moving=False):
        """Process new tape entries (and the price being answered, `extra`),
        with each round's peeks/swaps before that round's quotes."""
        if self.h0 is None:
            self.h0 = tuple(obs.hand)
        if self.sw is not None:
            self.newcard = obs.hand[self.sw[1]]
        tape = obs.tape
        n = len(tape)
        items = [(tape[j][0], j, tape[j]) for j in range(self.done, n)]
        if extra is not None:
            items.append((obs.round, n, (obs.round, "opp", extra, 0)))
        cur = obs.round - (1 if moving else 0)   # this round's moves are not out yet
        k = 0
        for r in range(self.mv_done + 1, cur + 1):
            while k < len(items) and items[k][0] < r:
                self._tape_ev(obs, items[k])
                k += 1
            self._move_ev(obs, r)
            self.mv_done = r
        while k < len(items):
            self._tape_ev(obs, items[k])
            k += 1
        self.done = n + (1 if extra is not None else 0)

    def _move_ev(self, obs, r):
        for rr, w in obs.peeks:
            if rr == r and w == "opp":
                self.ev.append(("peek", r))
                self._branch_peek(r)
        for rr, w, c in obs.discards:
            if rr == r and w == "opp":
                self.ev.append(("swap", r, c))
                self.hyps = [(t, pk, S, c) for t, pk, S, _ in self.hyps]

    def _branch_peek(self, r):
        """They peeked one of my cards: split each hypothesis by which one."""
        if self.dead:
            return
        hand_ids = []
        for slot in range(5):
            ep = 1 if (self.sw is not None and slot == self.sw[1] and r > self.sw[0]) else 0
            hand_ids.append((slot, ep))
        out = []
        seen = set()
        for t, pk, S, pend in self.hyps:
            fresh = [c for c in hand_ids if c not in pk] or hand_ids
            for c in fresh:
                npk = pk + (c,)
                key = (t, tuple(sorted(self._rank(x) * 10 + x[1] for x in npk)), S, pend)
                if key in seen:
                    continue
                seen.add(key)
                out.append((t, npk, S, pend))
        self.hyps = out[:MAX_HYPS]

    def _tape_ev(self, obs, item):
        r, j, (rr, w, px, q) = item
        v = self._view(obs, r, j)
        if w == "opp":
            self.ev.append(("q", r, px, v))
            self._filter_quote(r, px, v)
        else:
            self.ev.append(("m", r, px, q, v))
            mp = 0                              # my position before this trade
            for i in range(j):
                e_ = obs.tape[i]
                mp += e_[3] if e_[1] == "opp" else -e_[3]
            self.resp.append((r, v, px, q, -mp))

    def _pk(self, pk, r):
        s = 0
        n = 0
        for c in pk:
            if self._held(c, r):
                s += self._rank(c)
                n += 1
        return s, n

    def _filter_quote(self, r, px, v):
        """Keep hypotheses for which their quote implies a whole, consistent S."""
        if self.dead:
            return
        out = []
        shown, B, dsum, nd, plast = v
        for t, pk, S, pend in self.hyps:
            pkh, nkh = self._pk(pk, r) if pk else (0, 0)
            a, b = coef(t, shown, B, dsum, nd, plast, pkh, nkh)
            s = (px - a) / b
            si = round(s)
            if abs(s - si) * b > TOL or si < 6 or si > 64:
                continue
            if S is not None:
                if pend:                       # they swapped `pend` for a card of 1..13
                    d = si - S + pend
                    if d < 1 or d > 13:
                        continue
                elif si != S:
                    continue
            out.append((t, pk, si, 0))
        self.hyps = out
        if not out:
            self.dead = True

    def _best(self):
        if self.dead or not self.hyps or self.hyps[0][2] is None:
            return None
        best = None
        for h in self.hyps:
            w = TPRI.get(h[0], 1.0)
            if best is None or w > best[0]:
                best = (w, h)
        return best[1]

    def _alts(self):
        """Top-2 surviving hypotheses with distinct trust, with prior weights."""
        if self.dead or not self.hyps or self.hyps[0][2] is None:
            return []
        byt = {}
        for h in self.hyps:
            if h[0] not in byt:
                byt[h[0]] = h
        hs = sorted(byt.values(), key=lambda h: -TPRI.get(h[0], 1.0))[:2]
        tot = sum(TPRI.get(h[0], 1.0) for h in hs)
        return [(TPRI.get(h[0], 1.0) / tot, h) for h in hs]

    # ==================================================================
    #  valuation
    # ==================================================================
    @staticmethod
    def _pool(obs):
        us = obs.unseen
        U = 0
        U2 = 0
        C = 0
        for i in range(13):
            c = us[i]
            r = i + 1
            U += r * c
            U2 += r * r * c
            C += c
        return U, U2, C

    def _gauss(self, obs, honest, U, U2, C, t):
        """Fallback: Gaussian belief about their hand sum after all events.
        honest: their quotes are their fair (trust t) plus noise; else ignored.
        Their buy/sell/pass answers to my quotes are probit observations.
        Returns mean, variance, log-likelihood."""
        nk = len(obs.opp_known)
        ks = sum(obs.opp_known)
        k = 5 - nk
        mp = U / C
        vp = U2 / C - mp * mp
        mu = ks + k * mp
        v = k * vp * (C - k) / (C - 1)
        ll = 0.0
        sq2 = FB_SQ ** 2
        sr2 = FB_SR ** 2
        hmean = sum(obs.hand) / 5.0
        npk = 0
        for e in self.ev:
            kind = e[0]
            if kind == "peek":
                npk += 1
                continue
            if kind == "swap":
                mu += mp - e[2]
                v += vp
                continue
            if kind == "q":
                if not honest:
                    continue
                _, r, px, vw = e
                n_ = min(npk, 5)
                a, b = coef(t, vw[0], vw[1], vw[2], vw[3], vw[4], hmean * n_, n_)
                pred = a + b * mu
                sv = b * b * v + sq2
                kg = v * b / sv
                res = px - pred
                ll += -0.5 * res * res / sv - 0.5 * math.log(sv)
                mu += kg * res
                v -= kg * b * v
                continue
            _, r, px, qty, vw = e
            n_ = min(npk, 5)
            a, b = coef(t, vw[0], vw[1], vw[2], vw[3], vw[4], hmean * n_, n_)
            mF = a + b * mu
            sF2 = b * b * v
            st = math.sqrt(sF2 + sr2)
            if qty > 0:            # they bought: their fair > my price + 2
                c = (mF - px - 2.0) / st
                Z = max(Phi(c), 1e-12)
                lam = phi(c) / Z
                mF2 = mF + sF2 / st * lam
                vF2 = sF2 * (1.0 - sF2 / (st * st) * lam * (lam + c))
            elif qty < 0:          # they sold: their fair < my price - 2
                c = (px - 2.0 - mF) / st
                Z = max(Phi(c), 1e-12)
                lam = phi(c) / Z
                mF2 = mF - sF2 / st * lam
                vF2 = sF2 * (1.0 - sF2 / (st * st) * lam * (lam + c))
            else:                  # they passed: their fair within 2 of my price
                al = (px - 2.0 - mF) / st
                be = (px + 2.0 - mF) / st
                Z = max(Phi(be) - Phi(al), 1e-12)
                pa = phi(al)
                pb = phi(be)
                g = (pa - pb) / Z
                mF2 = mF + sF2 / st * g
                vF2 = sF2 * (1.0 - sF2 / (st * st) * ((be * pb - al * pa) / Z + g * g))
            ll += math.log(Z)
            if vF2 < 1e-6:
                vF2 = 1e-6
            mu = (mF2 - a) / b
            v = vF2 / (b * b)
        return mu, v, ll

    def _state(self, obs):
        """(E, exact hypothesis or None, their hand sum S, var(S), mean of unseen pool)."""
        U, U2, C = self._pool(obs)
        nk = len(obs.opp_known)
        ks = sum(obs.opp_known)
        hyp = self._best()
        if hyp is not None:
            S = float(hyp[2])
            var = 0.0
            if hyp[3]:                         # they swapped since their last quote
                S = S - hyp[3] + (U - (S - hyp[3] - ks)) / (C - (5 - nk) + 1)
                var = 14.0
        else:
            types = ((True, 0.8, FB_PH * 0.5), (True, 0.5, FB_PH * 0.25),
                     (True, 0.0, FB_PH * 0.25), (False, 0.8, 1 - FB_PH))
            res = []
            for hon, tt, pr in types:
                m_, v_, l_ = self._gauss(obs, hon, U, U2, C, tt)
                res.append((m_, v_, l_, tt, pr))
            mx = max(r[2] for r in res)
            ws = [r[4] * math.exp(r[2] - mx) for r in res]
            tw = sum(ws)
            S = 0.0
            M2 = 0.0
            te = 0.0
            for w, (m_, v_, l_, tt, pr) in zip(ws, res):
                w /= tw
                S += w * m_
                M2 += w * (v_ + m_ * m_)
                te += w * tt
            var = M2 - S * S
            self.t_eff = te
        pm = (U - (S - ks)) / (C - (5 - nk))
        E = sum(obs.hand) + sum(obs.board) + S + (5 - len(obs.board)) * pm
        return E, hyp, S, var, pm

    def _state_h(self, obs, hyp):
        U, U2, C = self._pool(obs)
        nk = len(obs.opp_known)
        ks = sum(obs.opp_known)
        S = float(hyp[2])
        if hyp[3]:
            S = S - hyp[3] + (U - (S - hyp[3] - ks)) / (C - (5 - nk) + 1)
        pm = (U - (S - ks)) / (C - (5 - nk))
        return sum(obs.hand) + sum(obs.board) + S + (5 - len(obs.board)) * pm, S, pm

    def _their_F(self, obs, hyp, S):
        """Their fair right now (as used to answer my next quote): (F, a, b)."""
        shown = len(obs.board)
        B = sum(obs.board)
        dsum = sum(c for _, _, c in obs.discards)
        nd = len(obs.discards)
        pl = self._my_last(obs)
        if hyp is not None:
            pkh, nkh = self._pk(hyp[1], obs.round) if hyp[1] else (0, 0)
            a, b = coef(hyp[0], shown, B, dsum, nd, pl, pkh, nkh)
        else:
            n_ = min(sum(1 for _, w in obs.peeks if w == "opp"), 5)
            a, b = coef(self.t_eff, shown, B, dsum, nd, pl, sum(obs.hand) / 5.0 * n_, n_)
        return a + b * S, a, b

    @staticmethod
    def _my_last(obs):
        pl = None
        for r, w, px, q in obs.tape:
            if w == "me":
                pl = px
        return pl

    def _seat(self, obs, quoting):
        if self.seat is None:
            tape = obs.tape
            if tape:
                self.seat = 0 if tape[0][1] == "me" else 1
            else:
                self.seat = 0 if quoting else 1

    # ==================================================================
    #  exact mode: their answers, then the planner
    # ==================================================================
    def _resp_model(self, hyp):
        """From their answers to my quotes (since their last swap): smallest edge
        they traded at, largest they passed at, and whether they size by edge."""
        trmin = 99.0
        psmax = 0.0
        self.full = False
        self.one = False
        t = hyp[0]
        S = hyp[2]
        last_sw = 0
        for e in self.ev:
            if e[0] == "swap":
                last_sw = e[1]
        for r, v, px, q, opos in self.resp:
            if r < last_sw or hyp[3]:
                continue
            pkh, nkh = self._pk(hyp[1], r) if hyp[1] else (0, 0)
            a, b = coef(t, v[0], v[1], v[2], v[3], v[4], pkh, nkh)
            es = a + b * S - px
            e = abs(es)
            if not q and ((es > 0 and opos >= 9) or (es < 0 and opos <= -9)):
                continue                       # a pass forced by the position limit
            if q:
                if e < trmin:
                    trmin = e
                if abs(q) == 1:
                    self.one = True
                elif e < 2.97:
                    self.full = True
            elif e > psmax:
                psmax = e
        self.rm = (trmin, psmax)

    def _band(self):
        return min(BAND, self.rm[0] - 0.05)

    def _hk(self, t):
        """Harvest: how far outside their fair to quote so they trade 2 lots."""
        th = max(2.0, self.rm[1])
        if self.full and not self.one:
            return th + 0.03
        if not self.one and t == 0.0:
            return th + 0.53                   # probe: does a t = 0 bot trade 2 lots here?
        return th + 1.03

    def _resp_lots(self, e):
        th = max(2.0, self.rm[1])
        ae = abs(e)
        if ae <= th:
            return 0
        n = 2 if ae >= th + 1.0 else 1
        return n if e > 0 else -n

    def _plan(self, obs, E, hyp, S, pm, cur_quote, cur_price, first_P=None):
        """Best plan for the rest of the deal under one hypothesis.

        Events are my quotes (kind 0) and theirs (kind 1) in play order. Each of
        my quotes either steers (no trade) or harvests (2 lots at about their
        fair); their quotes are taken when worth it. A plan fixes a direction d
        and a steer/harvest mask; trades fill the 10-lot capacity best edge first.
        Returns (value, d, mask, take the current quote?), or with first_P (my
        quote now fixed at that price) the plan's value only."""
        t = hyp[0]
        rnd = obs.round
        shown0 = len(obs.board)
        B0 = sum(obs.board)
        dsum = sum(c for _, _, c in obs.discards)
        nd = len(obs.discards)
        pkh, nkh = self._pk(hyp[1], rnd) if hyp[1] else (0, 0)
        pl0 = self._my_last(obs)
        ck = {}                                # their fair in round k: ck[k] + t * my last quote
        c0k = {}                               # ... before I have quoted at all
        for k in range(rnd, 6):
            shown = k - 1
            Bk = B0 + (shown - shown0) * pm
            a, b = coef(t, shown, Bk, dsum, nd, 0.0, pkh, nkh)
            ck[k] = a + b * S
            a0, b0 = coef(0.0, shown, Bk, dsum, nd, None, pkh, nkh)
            c0k[k] = a0 + b0 * S
        ev = []
        for k in range(rnd, 6):
            order = (0, 1) if self.seat == (k - 1) % 2 else (1, 0)
            for kind in order:
                ev.append((kind, k))
        ev = ev[ev.index((0, rnd) if cur_quote else (1, rnd)):]
        nmine = sum(1 for e in ev if e[0] == 0)
        pos = obs.position
        band = self._band()
        hk = self._hk(t)
        best = None
        imm = 0.0
        pos1 = pos
        if first_P is not None:
            Fr = c0k[rnd] if pl0 is None else ck[rnd] + t * pl0
            n = self._resp_lots(Fr - first_P)
            if n > 0:
                n = min(n, 10 + pos)
                imm = n * (first_P + 2.0 - E)
            elif n < 0:
                n = -min(-n, 10 - pos)
                imm = -n * (E - first_P + 2.0)
            pos1 = pos - n
        for d in (1, -1):
            cap = 10 - d * pos1
            if cap < 0:
                cap = 0
            for mask in range(1 << nmine):
                if first_P is not None and mask & 1:
                    continue
                plast = pl0
                mand = []
                opt = []
                bit = 0
                for j, (kind, k) in enumerate(ev):
                    if kind == 0:
                        Fr = c0k[k] if plast is None else ck[k] + t * plast
                        if j == 0 and first_P is not None:
                            P_ = first_P
                        elif (mask >> bit) & 1:
                            P_ = Fr + d * hk
                            mand.append(d * (E - P_) + 2.0)
                        else:
                            P_ = Fr - d * band
                        bit += 1
                        plast = P_
                    else:
                        if j == 0 and cur_price is not None:
                            q = cur_price
                        else:
                            q = c0k[k] if plast is None else ck[k] + t * plast
                        opt.append((d * (E - q) - 2.0, j))
                val = 0.0
                c = cap
                bad = False
                for edge in mand:
                    if edge <= 0:
                        bad = True
                        break
                    l = 2 if c >= 2 else c
                    val += edge * l
                    c -= l
                if bad:
                    continue
                opt.sort(reverse=True)
                take0 = False
                for edge, j in opt:
                    if edge <= 0 or c <= 0:
                        break
                    l = 2 if c >= 2 else c
                    val += edge * l
                    c -= l
                    if j == 0:
                        take0 = True
                if best is None or val > best[0]:
                    best = (val, d, mask, take0)
        if first_P is not None:
            return imm + (best[0] if best is not None else 0.0)
        return best

    # ==================================================================
    #  the three calls
    # ==================================================================
    def move(self, obs):
        try:
            return self._move(obs)
        except Exception:
            return None

    def quote(self, obs):
        try:
            return self._quote(obs)
        except Exception:
            return self._safe_fair(obs)

    def respond(self, obs, price):
        try:
            return self._respond(obs, price)
        except Exception:
            return 0

    @staticmethod
    def _safe_fair(obs):
        n = sum(obs.unseen)
        avg = sum((r + 1) * c for r, c in enumerate(obs.unseen)) / n
        hidden = 10 - len(obs.opp_known) - len(obs.board)
        return sum(obs.hand) + sum(obs.board) + sum(obs.opp_known) + hidden * avg

    def _move(self, obs):
        self._sync(obs, moving=True)
        if self.sw is not None or any(w == "me" for _, w, _ in obs.discards):
            return None
        E, hyp, S, var, pm = self._state(obs)
        hand = obs.hand
        lo = min(range(5), key=lambda i: hand[i])
        hi = max(range(5), key=lambda i: hand[i])
        pos = obs.position
        if hyp is not None:
            F = self._their_F(obs, hyp, S)[0]
            hs = self._alts()
            if len(hs) > 1:                    # trust still ambiguous: weigh the edge
                Dw = 0.0
                for w, h in hs:
                    Eh, Sh, pmh = self._state_h(obs, h)
                    Dw += w * (Eh - self._their_F(obs, h, Sh)[0])
                F = E - Dw
        elif not self.ev:
            F = E - 0.86 * (sum(hand) - 5 * pm)
        else:
            F = self._their_F(obs, None, S)[0]
        D = E - F                              # my edge: + means they undervalue
        if hyp is not None and hyp[0] == 0.0 and all(h[0] == 0.0 for h in self.hyps):
            # they ignore my quotes, so the edge is stable: make it as big as possible
            dl = D + (pm - hand[lo])
            ds = D - (hand[hi] - pm)
            if pos > 0 and ds < 0:
                ds = -99.0
            if abs(dl) >= abs(ds) and abs(dl) - abs(D) >= SWAP_MIN and (dl * D >= 0 or pos == 0):
                self.sw = (obs.round, lo)
                return ("SWAP", lo)
            if abs(ds) > abs(dl) and abs(ds) - abs(D) >= SWAP_MIN and (ds * D >= 0 or pos == 0):
                self.sw = (obs.round, hi)
                return ("SWAP", hi)
            return None
        d = 0
        if pos > 0 or (pos == 0 and hyp is not None and hyp[0] == 0.0 and D > SWAP_D0):
            d = 1
        elif pos < 0 or (pos == 0 and hyp is not None and hyp[0] == 0.0 and D < -SWAP_D0):
            d = -1
        if d > 0 and pm - hand[lo] >= SWAP_MIN:
            self.sw = (obs.round, lo)
            return ("SWAP", lo)
        if d < 0 and hand[hi] - pm >= SWAP_MIN:
            self.sw = (obs.round, hi)
            return ("SWAP", hi)
        return None

    def _quote(self, obs):
        self._seat(obs, True)
        self._sync(obs)
        E, hyp, S, var, pm = self._state(obs)
        if hyp is None:
            if not self.ev or all(e[0] != "q" and e[0] != "m" for e in self.ev):
                # nothing known yet: quote as if my hand were average
                return E - 0.86 * (sum(obs.hand) - 5 * pm)
            # fallback: quote around THEIR fair, offset for best expected profit
            F, a, b = self._their_F(obs, None, S)
            tau = math.sqrt(b * b * max(var, 0.0) + FB_SM ** 2)
            D = E - F
            bk = 0.0
            bv = None
            for i in range(-24, 25):
                k = i * 0.5
                A = k - 2.0
                Bk = k + 2.0
                pv = ((D - A) * Phi(A / tau) - tau * phi(A / tau)
                      + (Bk - D) * (1.0 - Phi(Bk / tau)) - tau * phi(Bk / tau))
                if bv is None or pv > bv:
                    bv, bk = pv, k
            sf = STEER_FB * min(1.0, self.t_eff / 0.8)
            if sf and abs(D) > 1.0:
                bk -= sf if D > 0 else -sf
            return F + bk
        self._resp_model(hyp)
        best = self._plan(obs, E, hyp, S, pm, True, None)
        Fr = self._their_F(obs, hyp, S)[0]
        if best is None:
            return Fr
        val, d, mask, _ = best
        Pq = Fr + d * self._hk(hyp[0]) if mask & 1 else Fr - d * self._band()
        hs = self._alts()
        if len(hs) > 1:
            # several trust values still fit and disagree about their fair:
            # score candidate prices under each, weighted by prior
            sts = []
            for w, h in hs:
                Eh, Sh, pmh = self._state_h(obs, h)
                Fh = self._their_F(obs, h, Sh)[0]
                sts.append((w, h, Eh, Sh, pmh, Fh))
            if max(abs(s[5] - Fr) for s in sts) > 0.3:
                cands = [Pq]
                for w, h, Eh, Sh, pmh, Fh in sts[1:]:
                    cands.append(min(max(Pq, Fh - 1.97), Fh + 1.97))
                    b2 = self._plan(obs, Eh, h, Sh, pmh, True, None)
                    if b2 is not None:
                        _, d2, m2, _ = b2
                        cands.append(Fh + d2 * 3.03 if m2 & 1 else Fh - d2 * 1.97)
                bestc = None
                for c in cands:
                    tot = 0.0
                    for w, h, Eh, Sh, pmh, Fh in sts:
                        tot += w * self._plan(obs, Eh, h, Sh, pmh, True, None, first_P=c)
                    if bestc is None or tot > bestc[0]:
                        bestc = (tot, c)
                Pq = bestc[1]
        return Pq

    def _respond(self, obs, price):
        self._seat(obs, False)
        self._sync(obs, price)
        E, hyp, S, var, pm = self._state(obs)
        if hyp is None:
            if E - price - 2 > FB_TAKE:
                return 2
            if price - 2 - E > FB_TAKE:
                return -2
            return 0
        self._resp_model(hyp)
        best = self._plan(obs, E, hyp, S, pm, False, price)
        if best is None:
            return 0
        return 2 * best[1] if best[3] else 0
