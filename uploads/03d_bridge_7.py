# Team Name: Alpha Rodeo
# Members: Jaiv Patel(26075057)
# Mentor: Arpit Gupta
# Upload note: bridge bot, pool about +7 (old_plan + identification + checked steering) (from zoo/bridge_7.py)

"""
bridge_7.py - a mid-strength test opponent ("bridge" between old_plan and the rivals).

BUILDING BLOCKS USED
  * zoo/old_plan.py  (the base, switches fixed at what its experiment loop kept)
      - every opponent quote is read with the board as it was then, newer quotes
        weighted more, and their swaps after a quote shift their hand by (m - card)
      - LEVEL-2 reading: their quote contains their view of OUR hand (from our
        last quote); that echo is removed before reading their hand
      - BOUNDS: their buy / sell / pass on our quotes bound their hand
      - swap on the expected FINAL position; expect a sharp-style opponent swap
      - quote noise +-0.5 and an inventory skew near the position limit
  * zoo/mid_steer.py (CHECKED steering, used only against reader-like opponents)
      - a reader moves its fair 0.8 of the way to what our last quote implies, so a
        quote just inside its no-trade band moves its belief without a trade
      - we predict each new quote of theirs from the previous one with that model;
        a miss marks them "alien" and steering is switched off for the deal
      - a trade through a steering quote also switches steering off
  * zoo/mid_exact.py (exact identification of reader-family hands)
      - a reader-family quote (any trust t on a 0..1 grid) is linear in its hand
        sum S; quotes are rounded to 0.01 and S is whole, so inverting each quote
        and keeping only consistent whole S pins the hand down exactly
      - our extension: the family also covers quotes shaded toward the public
        estimate, an expected-swap offset, and an early-round hand-signal flip
      - identified: value the stock with that S, trade 2 lots past the spread

WHEN WE STEER: only against a CHECKED reader, i.e. one whose hand is exactly
identified (then its fair is computed with its own formula; an exact fit beats
the looser reader-model check), or one that has passed MIN_CHECKS reader-model
predictions without a miss. Against everyone else (noisy, hiding, Bayesian,
steering or unknown bots) we play plain old_plan.

Measured (300 deals x seeds 1 2, pool score): old_plan +5.20; + checked steering
~0; + exact identification +0.3; + steering as soon as identified +0.9;
+ exact fair for steering +0.1; + wider family (shade / swap / bluff) +0.4;
+ identification overrides the reader-model check +0.1.  Total about +7.0.
"""

import random

# ── old_plan numbers ──────────────────────────────────────────────────
TRUST = 0.8           # how far to move from the prior toward what their quotes imply
T_ME = 1.0            # the trust we assume THEY put in our quotes (level-2 echo)
SWAP_GAIN = 30.0      # min expected gain (lots x points) to swap
SWAP_FROM = 3         # earliest round to swap
OPP_SWAP_K = 0.5      # scale of the expected opponent swap
NOISE = 0.5           # quote noise
SKEW = 0.2            # inventory skew once |position| >= 6

# ── mid_steer numbers ─────────────────────────────────────────────────
R_TRUST = 0.8         # a reader's trust in our last quote
EXACT_MARGIN = 1.9    # how far inside their band we quote when their fair is known exactly
APPROX_MARGIN = 1.6   # ...and when it is predicted across a board turn
ALIEN_TOL = 1.0       # reader-model miss (points) that marks them as not a reader
DECIDE_EDGE = 1.0     # |V - F| needed before committing to a steering direction
MIN_CHECKS = 2        # reader-model checks they must pass before we steer

# ── mid_exact numbers ─────────────────────────────────────────────────
T_GRID = [i / 10 for i in range(11)]   # trusts we test for: 0.0 .. 1.0
# Extension of mid_exact's family: the quote may also be shaded a fraction k toward
# the public estimate, and moved by +-g for an expected opponent swap (an AI-typical
# sharp variant), or flip its hand signal in rounds 1-2 by L x (S - 5m) (an early
# bluffer). Every combination is still linear in S, so it inverts the same way.
K_GRID = (0.0, 0.3)
G_GRID = (0.0, 3.9)
L_GRID = (0.0, 2.0)
LIE_ROUNDS = 2
FAMILY = [(t, k, g, L) for t in T_GRID for k in K_GRID for g in G_GRID for L in L_GRID
          if not (L and (k or g))]
TOL = 0.0051                           # quotes are rounded to 0.01
DECK_SUM = 4 * 91                      # sum of all 52 ranks


class Bot:
    def __init__(self):
        self.snap = {}       # round -> reader-model board terms that round
        self.dir = 0         # +1: steer their belief down (we buy), -1: up (we sell)
        self.off = False     # they traded through a steering quote
        self.alien = False   # their quotes do not follow ours like a reader's
        self.checked = 0     # how many of their quotes the model has looked at
        self.passed = 0      # how many reader-model predictions they matched
        self.steered = []    # for each of our quotes: was it a steering quote
        # exact identification state (mid_exact)
        self.cand = {f: None for f in FAMILY}  # (t, k, g, L) -> S at last quote (None = any)
        self.dead = False                      # no (t, S) fits: not reader-family
        self.done = 0                          # opponent quotes already processed
        self.last_round = 0                    # round of the last processed quote
        self.S = None                          # identified hand sum (at last quote)

    # ── small helpers (old_plan) ──────────────────────────────────────
    @staticmethod
    def avg(obs):
        return sum((r + 1) * c for r, c in enumerate(obs.unseen)) / sum(obs.unseen)

    @staticmethod
    def public(obs):
        """Value anyone can see: board + every other card at the public average."""
        ds = sum(c for _, _, c in obs.discards)
        nb, nd = len(obs.board), len(obs.discards)
        return sum(obs.board) + (15 - nb) * (364 - sum(obs.board) - ds) / (52 - nb - nd)

    @staticmethod
    def board_then(obs, r):
        """(board sum, hidden board cards) when a round-r quote was made."""
        return sum(obs.board[:r - 1]), 5 - (r - 1)

    def view_of_me(self, obs, upto, m):
        """Level-2: a reader's estimate of MY hand, from my last quote before tape index upto."""
        last = None
        for j in range(min(upto, len(obs.tape))):
            r, who, px, q = obs.tape[j]
            if who == "me":
                last = (r, px)
        if last is None:
            return 5 * m
        b, hb = self.board_then(obs, last[0])
        implied = last[1] - b - (5 + hb) * m
        return 5 * m + T_ME * (implied - 5 * m)

    @staticmethod
    def swap_shift(obs, r, m):
        """Their hand change from swaps they made after round r."""
        return sum(m - c for rd, who, c in obs.discards if who == "opp" and rd > r)

    # ── the opponent's hand (old_plan) ────────────────────────────────
    def opp_hand(self, obs, new_quote=None):
        m = self.avg(obs)
        prior = sum(obs.opp_known) + (5 - len(obs.opp_known)) * m
        tape = list(obs.tape)
        if new_quote is not None:
            tape.append((obs.round, "opp", new_quote, 0))

        # implied hand from each of their quotes, echo of our quotes removed
        imps = []
        for j, (r, who, px, q) in enumerate(tape):
            if who != "opp":
                continue
            b, hb = self.board_then(obs, r)
            h = px - b - self.view_of_me(obs, j, m) - hb * m
            imps.append(h + self.swap_shift(obs, r, m))
        est = prior
        if imps:
            ws = range(1, len(imps) + 1)
            implied = sum(w * x for w, x in zip(ws, imps)) / sum(ws)
            est = prior + TRUST * (implied - prior)

        # their answers to my quotes bound their hand
        lo, hi = 5.0, 65.0
        pos = 0                                       # my position before each entry
        for j, (r, who, px, q) in enumerate(obs.tape):
            if who == "me":
                opp_pos = -pos
                b, hb = self.board_then(obs, r)
                rest = b + self.view_of_me(obs, j, m) + hb * m - self.swap_shift(obs, r, m)
                if q > 0:
                    lo = max(lo, px + 2 - rest)
                elif q < 0:
                    hi = min(hi, px - 2 - rest)
                else:
                    if opp_pos < 10:                  # they could have bought
                        hi = min(hi, px + 2 - rest)
                    if opp_pos > -10:                 # they could have sold
                        lo = max(lo, px - 2 - rest)
                pos -= q
            else:
                pos += q
        if lo <= hi:
            est = min(hi, max(lo, est))
        return est

    def expected_opp_swap(self, obs, m):
        """Expected value change from a sharp-style opponent swap still to come."""
        if obs.round >= 5 or obs.position == 0:
            return 0.0
        if any(who == "opp" for _, who, _ in obs.discards):
            return 0.0
        pool = sorted(r + 1 for r, c in enumerate(obs.unseen) for _ in range(c))
        n = len(pool)
        if obs.position < 0:          # they are long: they throw a low card, value rises
            card = pool[n // 6]
            return OPP_SWAP_K * (m - card) if m - card > 3 else 0.0
        card = pool[(5 * n) // 6]     # they are short: they throw a high card, value falls
        return OPP_SWAP_K * (m - card) if card - m > 3 else 0.0

    def fair(self, obs, new_quote=None):
        m = self.avg(obs)
        hidden_board = 5 - len(obs.board)
        S = self.exact_S(obs)
        if S is not None:
            # Opponent hand known: hidden board cards average the rest of the unseen.
            U = sum((r + 1) * c for r, c in enumerate(obs.unseen))
            rest = (U - S) / (sum(obs.unseen) - 5)
            return sum(obs.hand) + sum(obs.board) + S + hidden_board * rest
        return (sum(obs.hand) + sum(obs.board) + self.opp_hand(obs, new_quote)
                + hidden_board * m + self.expected_opp_swap(obs, m))

    # ── reader model and its check (mid_steer) ────────────────────────
    def board_terms(self, obs):
        """g (board part of a reader's fair) and what blind_p0 needs."""
        m = self.avg(obs)
        hb = 5 - len(obs.board)
        B = sum(obs.board)
        T = sum((r + 1) * c for r, c in enumerate(obs.unseen)) + sum(obs.hand)
        return 0.2 * (B + hb * m) - 3 * m, (B, hb, T, sum(obs.unseen))

    @staticmethod
    def blind_p0(snap, q):
        """Before any quote of ours, a reader values our hand at 5 x ITS average
        unseen rank; solve its quote for its hand to get that 'virtual quote'."""
        B, hb, T, n = snap[1]
        H = (q - B - (5 + hb) * T / n) / (1 - (5 + hb) / n)
        return B + (10 + hb) * (T - H) / n

    def note_round(self, obs):
        # Called from quote/respond, so this round's swaps are already in.
        if obs.round not in self.snap:
            self.snap[obs.round] = self.board_terms(obs)

    @staticmethod
    def tape_view(obs):
        """Our quotes, and theirs as (price, round, index of our latest quote they had seen)."""
        mine, theirs = [], []
        for r, who, px, qty in obs.tape:
            if who == "me":
                mine.append(px)
            else:
                theirs.append((px, r, len(mine) - 1))
        return mine, theirs

    def our_seen(self, mine, idx, snap, q):
        return mine[idx] if idx >= 0 else self.blind_p0(snap, q)

    def check_reader(self, obs):
        """Predict each new quote of theirs from their previous one with the reader
        model. A miss (no swap / peek by them in between) marks them alien."""
        mine, theirs = self.tape_view(obs)
        acted = {r for r, who, _ in obs.discards if who == "opp"}
        acted |= {r for r, who in obs.peeks if who == "opp"}
        for j in range(max(1, self.checked), len(theirs)):
            (q0, r0, s0), (q1, r1, s1) = theirs[j - 1], theirs[j]
            if r0 in acted or r1 in acted or r0 not in self.snap or r1 not in self.snap:
                continue
            p0 = self.our_seen(mine, s0, self.snap[r0], q0)
            p1 = self.our_seen(mine, s1, self.snap[r1], q1)
            pred = q0 + R_TRUST * (p1 - p0) + self.snap[r1][0] - self.snap[r0][0]
            if abs(q1 - pred) > ALIEN_TOL:
                self.alien = True
            else:
                self.passed += 1
        self.checked = max(self.checked, len(theirs))

    def their_fair(self, obs):
        """(F, exact): a reader's fair right now, from its last quote shifted by
        0.8 x how far our quote moved since, plus the board change."""
        mine, theirs = self.tape_view(obs)
        if not theirs:
            return None, False
        F = self.exact_their_fair(obs, mine)
        if F is not None:
            return F, True
        q, qr, seen = theirs[-1]
        snap = self.snap.get(qr) or self.board_terms(obs)
        p_then = self.our_seen(mine, seen, snap, q)
        p_now = mine[-1] if mine else p_then
        F = q + R_TRUST * (p_now - p_then) + self.board_terms(obs)[0] - snap[0]
        return F, (qr == obs.round and seen == len(mine) - 1)

    def exact_their_fair(self, obs, mine):
        """An identified reader-family opponent's fair right now, computed with its
        own formula (its hand S, its trust t, today's board, our latest quote).
        None if not identified, if they swapped since (S no longer whole-known),
        or if the surviving trusts disagree."""
        if self.S is None or any(w == "opp" and r > self.last_round for r, w, _ in obs.discards):
            return None
        B, h = sum(obs.board), 5 - len(obs.board)
        D, N = sum(k for _, _, k in obs.discards), 47 - len(obs.board) - len(obs.discards)
        U0 = DECK_SUM - B - D
        P = mine[-1] if mine else None
        Fs = []
        if any(k for _, k, _, _ in self.cand):
            return None                        # shaded quoters: no steering model
        # Their trading fair: a bluff (L) only touches their quotes, but the
        # expected-swap term (g) is in their fair; its sign follows their position now.
        swapped = any(w == "me" for _, w, _ in obs.discards)
        side = 0 if swapped or obs.round >= 5 else (1 if obs.position > 0 else (-1 if obs.position < 0 else 0))
        for t, _, g, _ in self.cand:
            if P is None:
                c0, c1 = B, 5 + h
            else:
                c0, c1 = (1 - t) * B + t * P, 5 + h - t * (10 + h)
            Fs.append(self.S + c0 + c1 * (U0 - self.S) / N + g * side)
        if not Fs or max(Fs) - min(Fs) > 0.3:
            return None
        return sum(Fs) / len(Fs)

    # ── exact identification (mid_exact) ──────────────────────────────
    def invert(self, Q, fam, B, h, D, N, P, pub, side, rnd):
        """The whole S that makes a family-(t, k, g, L) quoter quote Q, or None.
        Its fair F = S + c0 + c1*(U0 - S)/N (m = (U0 - S)/N is its average unseen rank);
        its quote Q = (1-k)(F + g*side) + k*pub - L*(S - 5m) [L only in rounds 1-2]."""
        t, k, g, L = fam
        U0 = DECK_SUM - B - D
        if P is None:                          # no quote of ours yet: t plays no part
            c0, c1 = B, 5 + h
        else:
            c0, c1 = (1 - t) * B + t * P, 5 + h - t * (10 + h)
        if rnd > LIE_ROUNDS:
            L = 0.0

        def quote_of(S):
            m = (U0 - S) / N
            return (1 - k) * (S + c0 + c1 * m + g * side) + k * pub - L * (S - 5 * m)

        q0 = quote_of(0)
        slope = quote_of(1) - q0               # Q is linear in S
        if abs(slope) < 1e-9:
            return None
        S = round((Q - q0) / slope)
        if not 5 <= S <= 65:
            return None
        return S if abs(quote_of(S) - Q) <= TOL else None

    def observe(self, F, rnd, board, discards, P, opp_pos):
        """Filter the (t, S) candidates with one opponent quote F made in round rnd."""
        self.done += 1
        if self.dead:
            return
        B, h = sum(board[:rnd - 1]), 5 - (rnd - 1)
        ds = [(r, w, k) for r, w, k in discards if r <= rnd]
        D, N = sum(k for _, _, k in ds), 47 - (rnd - 1) - len(ds)
        olds = [k for r, w, k in ds if w == "opp" and r > self.last_round]
        self.last_round = rnd
        # public estimate then, and which way an expected-swap term would push them
        pub = B + (15 - (rnd - 1)) * (DECK_SUM - B - D) / (52 - (rnd - 1) - len(ds))
        # (The AI-typical version keys this on whether its OPPONENT, i.e. we, swapped.)
        swapped = any(w == "me" for _, w, _ in ds)
        side = 0 if swapped or rnd >= 5 else (1 if opp_pos < 0 else (-1 if opp_pos > 0 else 0))
        new = {}
        for t, prev in self.cand.items():
            S = self.invert(F, t, B, h, D, N, P, pub, side, rnd)
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
        quotes, P, pos = [], None, 0             # pos: our position before each entry
        for r, who, px, q in obs.tape:
            if who == "me":
                P = px
                pos -= q
            else:
                quotes.append((px, r, P, -pos))
                pos += q
        if pending is not None:
            quotes.append((pending, obs.round, P, -pos))
        for px, r, p, opp_pos in quotes[self.done:]:
            self.observe(px, r, obs.board, obs.discards, p, opp_pos)

    def exact_S(self, obs):
        """The opponent's current hand sum if identified (expected, if they just swapped)."""
        if self.S is None:
            return None
        S = self.S
        for r, w, k in obs.discards:
            if w == "opp" and r > self.last_round:
                S += self.avg(obs) - k
        return S

    # ── the three calls ───────────────────────────────────────────────
    def move(self, obs):
        try:
            return self._move(obs)
        except Exception:
            return None

    def quote(self, obs):
        try:
            return self._quote(obs)
        except Exception:
            self.steered.append(False)
            m = self.avg(obs)
            return sum(obs.hand) + sum(obs.board) + (10 - len(obs.board)) * m

    def respond(self, obs, price):
        try:
            self.note_round(obs)
            self.check_reader(obs)
            self.sync(obs, pending=price)
            return self._respond(obs, price)
        except Exception:
            return 0

    def _move(self, obs):
        self.sync(obs)
        # old_plan: swap on the expected final position, from round 3
        if any(who == "me" for _, who, _ in obs.discards) or obs.round < SWAP_FROM:
            return None
        m = self.avg(obs)
        hand = obs.hand
        opp_q = [px for r, who, px, q in obs.tape if who == "opp"]
        edge = self.fair(obs) - (opp_q[-1] if opp_q else self.public(obs))
        rounds_left = 5 - obs.round + 1
        step = 1 if edge > 0 else (-1 if edge < 0 else 0)
        final = max(-10, min(10, obs.position + rounds_left * 2 * step))
        best_i = max(range(5), key=lambda i: final * (m - hand[i]))
        if final * (m - hand[best_i]) > SWAP_GAIN:
            return ("SWAP", best_i)
        return None

    def _steer_price(self, obs, V):
        """mid_steer: a price just inside a CHECKED reader's no-trade band, or None.
        Checked = exactly identified, or (not alien and MIN_CHECKS model hits)."""
        if self.off or obs.round >= 5 or (self.S is None and (self.alien or self.passed < MIN_CHECKS)):
            return None
        # A trade on our last steering quote: no reader with a 2-wide band.
        mine_q = [qty for r, who, px, qty in obs.tape if who == "me"]
        if mine_q and mine_q[-1] and self.steered and self.steered[-1]:
            self.off = True
            return None
        F, exact = self.their_fair(obs)
        if F is None:
            return None
        if not self.dir and abs(V - F) > DECIDE_EDGE:
            self.dir = 1 if V > F else -1             # chosen once per deal
        room = 10 - obs.position if self.dir > 0 else 10 + obs.position
        if self.dir and room > 0 and self.dir * (V - F) > 0:
            return F - self.dir * (EXACT_MARGIN if exact else APPROX_MARGIN)
        return None

    def _quote(self, obs):
        self.note_round(obs)
        self.check_reader(obs)
        self.sync(obs)
        V = self.fair(obs)
        p = self._steer_price(obs, V)
        if p is not None:
            self.steered.append(True)
            return p
        # old_plan's defended honest quote: inventory skew + noise
        self.steered.append(False)
        q = V
        if abs(obs.position) >= 6:
            q -= SKEW * obs.position
        return q + random.uniform(-NOISE, NOISE)

    def _respond(self, obs, price):
        edge = self.fair(obs, price) - price
        if self.S is not None:                     # identified: full size past the spread
            return 2 if edge > 2 else (-2 if edge < -2 else 0)
        lots = int(abs(edge) - 2) + 1 if abs(edge) > 2 else 0
        return min(2, lots) * (1 if edge > 0 else -1)
