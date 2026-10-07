# Team Name: Alpha Rodeo
# Members: Jaiv Patel(26075057)
# Mentor: Arpit Gupta
# Upload note: probe - steering bot: huge wins only against teams that read our quotes (from zoo/mid_steer.py)

"""
mid_steer.py - reader's read of the opponent, sharp's swap, plus STEERING.

A reader-type opponent treats our last quote as our honest fair value and
moves its own fair 0.8 of the way towards what that quote implies. So if we
quote just inside its no-trade band (within 2 of its fair) it does not trade,
but its belief about our hand moves, and its NEXT quote moves with it.

  * Model the opponent's fair:  F = their hand + 0.8 * (our last quote) + g
    with g = 0.2 * (board + hidden_board * m) - 3 * m  (reader's formula, expanded).
    Calibrate it on their last quote, so their unknown hand cancels out.
  * Once our fair V and their F differ, pick a direction once: V > F means we
    want to buy, so steer their belief DOWN (quote F - margin); V < F, steer UP.
  * Take their quotes whenever the edge beats the spread (sharp's sizing).
  * Our final quote of the deal, or when steering no longer helps, is honest.
  * When reading their quote we remove the part our own lie put there.
  * If their quotes do not follow the reader model, or they trade through a
    steering quote, we stop relying on the model.
"""

TRUST = 0.8          # reader's trust in the other side's last quote
SWAP_EDGE = 3        # sharp's swap rule
EXACT_MARGIN = 1.9   # how far inside their band we quote when F is known exactly
APPROX_MARGIN = 1.6  # ...and when F is a prediction across a board turn
ALIEN_TOL = 1.0      # reader-model miss (points) that marks them as not a reader
DECIDE_EDGE = 1.0    # |V - F| needed before we commit to a steering direction


class Bot:
    def __init__(self):
        self.lies = []       # for each of our quotes: price - our fair then
        self.snap = {}       # round -> board terms of the reader model that round
        self.dir = 0         # +1: steer them down (we buy), -1: steer up (we sell)
        self.off = False     # they traded through a steering quote
        self.alien = False   # their quotes do not follow ours like a reader's
        self.checked = 0     # how many of their quotes the model has checked

    # ---- card counting and the reader model's board terms ----------------
    def avg(self, obs):
        return sum((r + 1) * c for r, c in enumerate(obs.unseen)) / sum(obs.unseen)

    def board_terms(self, obs):
        """g (board part of a reader's fair) and what blind_p0 needs."""
        m = self.avg(obs)
        hb = 5 - len(obs.board)
        B = sum(obs.board)
        T = sum((r + 1) * c for r, c in enumerate(obs.unseen)) + sum(obs.hand)
        return 0.2 * (B + hb * m) - 3 * m, (B, hb, T, sum(obs.unseen))

    def blind_p0(self, snap, q):
        """Before any quote of ours, a reader values our hand at 5 x ITS average
        unseen rank, the same as reading a quote P0. Its average is not ours (it
        sees its hand, not ours), so solve its quote q = H + B + (5+hb)(T-H)/n
        for its hand H, where T = our unseen + our hand."""
        B, hb, T, n = snap[1]
        H = (q - B - (5 + hb) * T / n) / (1 - (5 + hb) / n)
        return B + (10 + hb) * (T - H) / n

    def note_round(self, obs):
        # Called from quote/respond, so this round's swaps are already in.
        if obs.round not in self.snap:
            self.snap[obs.round] = self.board_terms(obs)

    # ---- the tape ---------------------------------------------------------
    def tape_view(self, obs):
        """Our quotes, and their quotes as (price, round, index of the latest
        quote of ours they had seen then, or -1)."""
        mine, theirs = [], []
        for r, who, px, qty in obs.tape:
            if who == "me":
                mine.append(px)
            else:
                theirs.append((px, r, len(mine) - 1))
        return mine, theirs

    def our_seen(self, mine, idx, snap, q):
        """The quote of ours a reader was reacting to (P0 if none yet)."""
        return mine[idx] if idx >= 0 else self.blind_p0(snap, q)

    def check_reader(self, obs):
        """Predict each new quote of theirs from their previous one with the
        reader model. A miss (no swap or peek by them in between) means they
        are not a reader: no more predictions across board turns, and no more
        undoing our lies when reading them."""
        mine, theirs = self.tape_view(obs)
        acted = {r for r, who, _ in obs.discards if who == "opp"}
        acted |= {r for r, who in obs.peeks if who == "opp"}
        for j in range(max(1, self.checked), len(theirs)):
            (q0, r0, s0), (q1, r1, s1) = theirs[j - 1], theirs[j]
            if r0 in acted or r1 in acted or r0 not in self.snap or r1 not in self.snap:
                continue
            p0 = self.our_seen(mine, s0, self.snap[r0], q0)
            p1 = self.our_seen(mine, s1, self.snap[r1], q1)
            pred = q0 + TRUST * (p1 - p0) + self.snap[r1][0] - self.snap[r0][0]
            if abs(q1 - pred) > ALIEN_TOL:
                self.alien = True
        self.checked = len(theirs)

    # ---- our fair value: reader's read, minus our own lie -----------------
    def fair(self, obs):
        m = self.avg(obs)
        hb = 5 - len(obs.board)
        opp_hand = sum(obs.opp_known) + (5 - len(obs.opp_known)) * m
        mine, theirs = self.tape_view(obs)
        if theirs:
            q, _, seen = theirs[-1]
            if seen >= 0 and not self.alien:
                q -= TRUST * self.lies[seen]   # 0.8 of our lie is in their quote
            implied = q - sum(obs.board) - (5 + hb) * m
            opp_hand += TRUST * (implied - opp_hand)
        return sum(obs.hand) + sum(obs.board) + opp_hand + hb * m

    # ---- their fair right now, if they are a reader ------------------------
    def their_fair(self, obs):
        """(F, exact). Exact when they quoted this round after our latest quote:
        then F is just their quote. Otherwise shift their last quote by 0.8 x
        how far our quote moved since, plus the board change."""
        mine, theirs = self.tape_view(obs)
        if not theirs:
            return None, False
        q, qr, seen = theirs[-1]
        snap = self.snap.get(qr) or self.board_terms(obs)
        p_then = self.our_seen(mine, seen, snap, q)
        p_now = mine[-1] if mine else p_then
        F = q + TRUST * (p_now - p_then) + self.board_terms(obs)[0] - snap[0]
        return F, (qr == obs.round and seen == len(mine) - 1)

    # ---- the three methods --------------------------------------------------
    def move(self, obs):
        # sharp's swap: long -> throw a low card, short -> throw a high one.
        if any(who == "me" for _, who, _ in obs.discards):
            return None
        m = self.avg(obs)
        lo = min(range(5), key=lambda i: obs.hand[i])
        hi = max(range(5), key=lambda i: obs.hand[i])
        if obs.position > 0 and obs.hand[lo] < m - SWAP_EDGE:
            return ("SWAP", lo)
        if obs.position < 0 and obs.hand[hi] > m + SWAP_EDGE:
            return ("SWAP", hi)
        return None

    def quote(self, obs):
        self.note_round(obs)
        self.check_reader(obs)
        V = self.fair(obs)
        # A trade on our last steering quote: they are no reader with a 2-wide
        # band, so stop steering for the rest of the deal.
        last_qty = [qty for r, who, px, qty in obs.tape if who == "me"][-1:]
        if last_qty and last_qty[0] and self.dir and abs(self.lies[-1]) > 0.5:
            self.off = True
        price = V                                     # honest by default
        F, exact = self.their_fair(obs)
        if F is not None and obs.round < 5 and not self.off and (exact or not self.alien):
            if not self.dir and abs(V - F) > DECIDE_EDGE:
                self.dir = 1 if V > F else -1         # chosen once per deal
            room = 10 - obs.position if self.dir > 0 else 10 + obs.position
            # Steer only while the edge still points our way and we can trade.
            if self.dir and room > 0 and self.dir * (V - F) > 0:
                price = F - self.dir * (EXACT_MARGIN if exact else APPROX_MARGIN)
        self.lies.append(price - V)
        return price

    def respond(self, obs, price):
        self.note_round(obs)
        self.check_reader(obs)
        edge = self.fair(obs) - price               # sharp's sizing
        lots = int(abs(edge) - 2) + 1 if abs(edge) > 2 else 0
        return min(2, lots) * (1 if edge > 0 else -1)
