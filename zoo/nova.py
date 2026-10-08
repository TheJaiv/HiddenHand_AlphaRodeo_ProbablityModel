# Team Name: Nova
# Members: Name 1 (Roll No.), Name 2 (Roll No.), Name 3 (Roll No.)
# Mentor: Your Mentor's Name

# ---------------------------------------------------------------------------
# NOVA - Hidden Hand bot
#
# Core: fair value = my cards + board + posterior estimate of the opponent's
# hand + average for hidden board cards.
#
# What makes Nova stronger than a plain card counter:
#   1. Bayesian blend of the opponent's hand sum from MANY clues:
#        - their quotes (corrected for board, their swap and their inventory)
#        - whether they bought / sold / passed on MY quotes (a pass means their
#          value sits inside my +-2 band, a trade means it is outside it)
#        - cards I peeked (exact)
#   2. Expects the opponent to swap (their position is the mirror of mine).
#   3. Hides my own hand a little when quoting, skews quotes by inventory.
#   4. Risk-aware sizing: demands more edge to add to a big position, less to
#      reduce it, more if the opponent has peeked at me.
#   5. Early peeks, and a swap used only when position x improvement is worth it.
#
# All tunables are the constants below.
# ---------------------------------------------------------------------------

SPREAD = 2.0
LIMIT = 10

# --- opponent-hand inference
RANK_VAR = 14.0        # variance of a single card rank
NOISE_VAR = 25.0       # noise of an opponent quote as a hand-sum clue
TRADE_VAR = 40.0       # noise of "they bought/sold on my quote" clue
PASS_VAR = 30.0        # noise of "they passed on my quote" clue
OVERSHOOT = 2.0        # when they trade, how far past my band they likely are
OPP_SKEW = 0.10        # assumed inventory skew in the opponent's quotes
CORR_DISCOUNT = 0.5    # repeated clues come from the same hand: count them half

# --- opponent swap expectation
P_OPP_SWAP = 0.5
OPP_SWAP_GAIN = 2.5

# --- quoting
SHRINK = 0.8           # hide my hand: pull quote toward what they would guess blind (big win in tests)
SKEW = 0.25            # per lot of inventory

# --- taking
MARGIN = 0.5           # base edge needed beyond the spread
BIG_EDGE = 2.0         # edge above this -> 2 lots
RISK_ADD = 1.0         # extra margin when adding to a full position
RISK_REDUCE = 0.3      # margin discount when reducing a full position
PEEKED_AT_PENALTY = 0.25   # per opponent peek on me

# --- moves
PEEK_ROUNDS = ()        # peeking cost more than it earned in my tests; try (1,) to experiment
MAX_PEEKS = 1
SWAP_MIN_GAIN = {2: 9.0, 3: 6.0, 4: 4.0, 5: 2.5}


def _g(obs, key, default=None):
    """Read a field whether obs is a dict or an object."""
    try:
        return obs[key]
    except Exception:
        return getattr(obs, key, default)


def _clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


class Bot:
    def __init__(self):
        # Per-deal memory only (a new Bot is built every deal).
        self.taker_total = 0     # lots I took as taker so far
        self.my_quotes = {}      # round -> price I quoted
        self.m_at = {}           # round -> lots I got as maker before this round
        self.pos_at = {}         # round -> my position at start of round

    # ------------------------------------------------------------- bookkeeping
    def _sync(self, obs):
        rnd = _g(obs, "round", 1) or 1
        pos = _g(obs, "position", 0) or 0
        if rnd not in self.m_at:
            self.m_at[rnd] = pos - self.taker_total
            self.pos_at[rnd] = pos

    def _avg_unseen(self, obs):
        unseen = list(_g(obs, "unseen", []) or [])
        total = sum(unseen)
        if total <= 0:
            return 7.0
        return sum((i + 1) * c for i, c in enumerate(unseen)) / total

    # ------------------------------------------------------------------ model
    def _value(self, obs, extra_quote=None):
        """Return (fair value, my hand's excess over average)."""
        hand = list(_g(obs, "hand", []) or [])
        board = list(_g(obs, "board", []) or [])
        known = list(_g(obs, "opp_known", []) or [])
        tape = list(_g(obs, "tape", []) or [])
        discards = list(_g(obs, "discards", []) or [])
        rnd = _g(obs, "round", 1) or 1
        pos = _g(obs, "position", 0) or 0

        avg = self._avg_unseen(obs)
        n_hidden = max(0, 5 - len(board))
        n_unk = max(0, 5 - len(known))
        prior_T = sum(known) + n_unk * avg
        var_prior = n_unk * RANK_VAR

        opp_disc = []
        for d in discards:
            try:
                if d[1] == "opp":
                    opp_disc.append((int(d[0]), float(d[2])))
            except Exception:
                continue

        def to_hand_sum(k, v_opp):
            """Convert 'opponent's fair value at round k' into their hand sum now."""
            b_k = sum(board[:max(0, k - 1)])
            unknown_to_them = 5 + max(0, 6 - k)
            s = v_opp - b_k - unknown_to_them * avg
            for r, rank in opp_disc:
                if k < r:                       # clue predates their swap
                    s += avg - rank
            return _clamp(s, 5.0, 65.0)

        signals = []   # (hand-sum estimate, variance)

        # Clue 1: opponent's quotes as maker
        quotes = []
        for t in tape:
            try:
                if t[1] == "opp":
                    quotes.append((int(t[0]), float(t[2])))
            except Exception:
                continue
        if extra_quote is not None:
            r, p = extra_quote
            if not any(qr == r and abs(qp - p) < 1e-9 for qr, qp in quotes):
                quotes.append((r, p))
        for k, q in quotes:
            their_pos = -self.pos_at.get(k, pos if k == rnd else 0)
            v_opp = q + OPP_SKEW * their_pos      # undo their assumed inventory skew
            signals.append((to_hand_sum(k, v_opp), NOISE_VAR))

        # Clue 2: what they did on MY quotes (bought / sold / passed)
        for k, p in self.my_quotes.items():
            if k >= rnd or k not in self.m_at or (k + 1) not in self.m_at:
                continue
            if abs(self.pos_at.get(k, 0)) >= 9:   # limits may have clipped the fill
                continue
            fill = self.m_at[k + 1] - self.m_at[k]   # lots I received as maker
            opp_qty = -fill                           # + means they bought from me
            if opp_qty > 0:
                center, var = p + SPREAD + OVERSHOOT, TRADE_VAR
            elif opp_qty < 0:
                center, var = p - SPREAD - OVERSHOOT, TRADE_VAR
            else:
                center, var = p, PASS_VAR
            signals.append((to_hand_sum(k, center), var))

        # Combine into a posterior for the opponent's hand sum
        T = prior_T
        if signals and n_unk > 0:
            precs = sorted((1.0 / v for _, v in signals), reverse=True)
            p_eff = precs[0] + CORR_DISCOUNT * sum(precs[1:])
            wsum = sum(1.0 / v for _, v in signals)
            mean = sum(s / v for s, v in signals) / wsum
            w = p_eff / (p_eff + 1.0 / var_prior)
            T = prior_T + w * (mean - prior_T)

        V = sum(hand) + sum(board) + T + n_hidden * avg

        # Expect the opponent to swap toward their own position (theirs = -mine)
        opp_swapped = len(opp_disc) > 0
        if not opp_swapped and rnd <= 4:
            V += P_OPP_SWAP * _clamp(-pos / 6.0, -1.0, 1.0) * OPP_SWAP_GAIN

        excess = sum(hand) - len(hand) * avg
        return V, excess

    # -------------------------------------------------------------------- API
    def move(self, obs):
        try:
            self._sync(obs)
            rnd = _g(obs, "round", 1) or 1
            hand = list(_g(obs, "hand", []) or [])
            pos = _g(obs, "position", 0) or 0
            discards = list(_g(obs, "discards", []) or [])
            peeks = list(_g(obs, "peeks", []) or [])

            # Swap (once): improve the value of the position I'm actually holding.
            already = any(len(d) > 1 and d[1] == "me" for d in discards)
            if not already and hand and pos != 0 and rnd in SWAP_MIN_GAIN:
                avg = self._avg_unseen(obs)
                if pos > 0:
                    i = min(range(len(hand)), key=lambda j: hand[j])
                    delta = avg - hand[i]
                else:
                    i = max(range(len(hand)), key=lambda j: hand[j])
                    delta = hand[i] - avg
                if abs(pos) * delta >= SWAP_MIN_GAIN[rnd]:
                    return ("SWAP", i)

            # Peek early
            my_peeks = sum(1 for p in peeks if len(p) > 1 and p[1] == "me")
            known = list(_g(obs, "opp_known", []) or [])
            if rnd in PEEK_ROUNDS and my_peeks < MAX_PEEKS and len(known) < 4:
                return "PEEK"
        except Exception:
            pass
        return None

    def quote(self, obs):
        try:
            self._sync(obs)
            rnd = _g(obs, "round", 1) or 1
            pos = _g(obs, "position", 0) or 0
            V, excess = self._value(obs)
            p = float(V - SHRINK * excess - SKEW * pos)
            self.my_quotes[rnd] = p
            return p
        except Exception:
            return 105.0

    def respond(self, obs, price):
        try:
            self._sync(obs)
            rnd = _g(obs, "round", 1) or 1
            pos = _g(obs, "position", 0) or 0
            peeks = list(_g(obs, "peeks", []) or [])
            opp_peeks = sum(1 for p in peeks if len(p) > 1 and p[1] == "opp")

            V, _ = self._value(obs, extra_quote=(rnd, price))
            buy_edge = V - (price + SPREAD)
            sell_edge = (price - SPREAD) - V

            def margin(direction):
                m = MARGIN + PEEKED_AT_PENALTY * opp_peeks
                load = abs(pos) / float(LIMIT)
                if direction * pos > 0:
                    m += RISK_ADD * load
                elif direction * pos < 0:
                    m -= RISK_REDUCE * load
                return max(0.1, m)

            n = 0
            if buy_edge >= sell_edge and buy_edge > margin(+1):
                n = 2 if buy_edge > BIG_EDGE else 1
                n = max(0, min(n, LIMIT - pos))
            elif sell_edge > buy_edge and sell_edge > margin(-1):
                n = 2 if sell_edge > BIG_EDGE else 1
                n = -max(0, min(n, LIMIT + pos))
            self.taker_total += n
            return n
        except Exception:
            return 0
