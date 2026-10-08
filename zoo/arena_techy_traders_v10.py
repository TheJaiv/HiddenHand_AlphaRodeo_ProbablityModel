# Team Name: Zoo - arena_techy_traders_v10
# Members: Organisers
# Mentor: None

"""
arena_techy_traders_v10.py - imitation of arena team "Techy Traders" v10 (entry #420), decoded
from its public replays (zoo/arena_raw/techy_traders/420_*.json, 81 fights). Live: mean +5.02,
house naive +8.14, reader +10.30, sharp +9.78; beats Alpha Rodeo hunt_v02 (#393 / #448) by +1.44;
loses to Cyberpsycho (-5.12), MNC (-2.81), Quants Treasure (-2.09), TeenPatti (-1.62), Genz7 (-1.20).

What the replays show (v10 dropped v9's "quote 0.00 to crush readers" weapon):
  * First quote: the public estimate + 0.7 (105.71 at the start).
  * Later quotes: about half its own value, half the opponent's predicted fair (their last quote
    carried for the cards turned since); against the house bots they sit 1-3 points from the
    opponent's fair, just past the +-2 band when it wants a trade.
  * It READS our quotes (trust ~0.8, including the price it is answering) but almost never takes:
    it trades only on an edge of about 7 points. Steerable by quotes, hard to pick off.
  * Swaps in round 5 when holding a position (127/132 swaps).

Fit: 96% of its take/pass decisions and 99% of swap decisions reproduced from the replays,
quotes within 1.1 on average. Calibrated (300 deals, seeds 71 72): naive +8.18, reader +10.38,
sharp +9.78, vs versions/hunt_v02.py +1.44 - all within 0.1 of live.
"""

LIM = 10
DECK = 364  # sum of all 52 ranks


def _avg(un):
    n = sum(un)
    return sum((r + 1) * c for r, c in enumerate(un)) / n if n else 7.0


class Bot:
    # calibrated on the replays and the arena scores (see the docstring)
    P = dict(
        T=0.79,             # trust in their quotes for my fair
        T_PRICE=True,       # respond(): read the price being answered as their newest quote
        R1_QUOTE='pub',     # first quote with no info: "pub", "nf", "nf+X"
        R1_ADD=0.7,         # added to that first quote
        W=0.555,            # quote = (1-W)*(F - SKEW_Q*pos) + W*P + C_Q
        SKEW_Q=0.079,       # quote: my value moves this much against each lot I hold
        C_Q=0.446,          # quote: constant offset
        HIDE=0.033,         # subtract HIDE * (my hand - 5m) from the quote
        SNAP=None,          # if set: |quote - P| beyond SNAP_IN -> P +- SNAP (trade at the band edge)
        SNAP_IN=1.95,       # ... (unused when SNAP is None)
        SKEW_R=-0.078,      # respond: fair - SKEW_R*pos
        TH1=6.805,          # respond: 1 lot if edge > TH1
        TH2=7.531,          # respond: 2 lots if edge > TH2
        R1_MAXLOT=2,        # most lots it takes in round 1
        SWAP='round',       # "sharp" (any round, card beyond m +- 3), "r5", "r5pos3"
        AVG_Q=3,            # average the hand read from their last AVG_Q quotes
        TRADE_EV=0.539,     # their hand estimate moves this much per lot they bought (+) / sold (-) on my quotes
        AGGRO_K=0.0,        # if set: quote = P + d*AGGRO_K, d = side of my position (or of F - P when flat)
        AGGRO_LIM=10,       # ... while |position| < AGGRO_LIM
        TB=0,               # 1: their trades on my quotes bound their predicted fair P
        TB_G=0.136,         # ... margin past the traded price
        TB_F=0.053,         # weight of "their hand read from the bounded P" in my value F
        SWAP_R=5,           # SWAP="round": swap from this round on ...
        SWAP_G=0,           # ... once the card is this far from the average (lowest if long, highest if short)
        SWAP_FLAT=0,        # 1: also swap when flat (the card furthest from average)
        MIRROR=0,           # 1: quote exactly their last quote (once they have quoted)
    )

    def __init__(self):
        self.prev_hand = None
        self.my_swap = None   # (round, out_rank, in_rank)

    # ------------------------------------------------------------ bookkeeping
    def _track(self, obs):
        """Remember my own swap: which card came in (only I ever see it)."""
        if self.my_swap is None and self.prev_hand is not None and obs.hand != self.prev_hand:
            for a, b in zip(self.prev_hand, obs.hand):
                if a != b:
                    r = next((r for r, w, c in obs.discards if w == "me"), obs.round)
                    self.my_swap = (r, a, b)
                    break
        self.prev_hand = obs.hand

    def _unseen_at(self, obs, rnd):
        """My unseen counts when quotes of round rnd were made."""
        un = list(obs.unseen)
        nb = rnd - 1
        for c in obs.board[nb:]:
            un[c - 1] += 1
        for r, w, c in obs.discards:
            if r > rnd and w == "opp":
                un[c - 1] += 1
        if self.my_swap and self.my_swap[0] > rnd and self.my_swap[2] is not None:
            un[self.my_swap[2] - 1] += 1      # my new card was still unseen then
        return un

    def _quote_excess(self, obs, rnd, q):
        """Their quote q in round rnd -> implied hand - 5m (reader formula, trust 1)."""
        m = _avg(self._unseen_at(obs, rnd))
        nb = rnd - 1
        B = sum(obs.board[:nb])
        return q - B - (15 - nb) * m

    def _opp_quotes(self, obs):
        return [(r, px) for r, w, px, q in obs.tape if w == "opp"]

    def fair(self, obs, price=None):
        p = self.P
        un = obs.unseen
        m = _avg(un)
        hb = 5 - len(obs.board)
        oq = self._opp_quotes(obs)
        if price is not None and p["T_PRICE"]:
            oq = oq + [(obs.round, price)]
        H_o = 5 * m
        if oq:
            use = oq[-p["AVG_Q"]:]
            H_o += p["T"] * sum(self._quote_excess(obs, r, q) for r, q in use) / len(use)
            r = use[0][0]
            for rr, w, c in obs.discards:          # they swapped since: old card out, ~m in
                if w == "opp" and rr > r:
                    H_o += m - c
        if p["TRADE_EV"]:
            H_o += p["TRADE_EV"] * sum(q for r, w, px, q in obs.tape if w == "me")
        P = self.pred_opp(obs) if p["TB_F"] else None
        if P is None and p["TB_F"] and price is not None and p["T_PRICE"]:
            P = price
        if P is not None:
            H_p = P - sum(obs.board) - (10 - len(obs.board)) * m   # their hand if P is their fair
            H_o += p["TB_F"] * (H_p - H_o)
        return sum(obs.hand) + sum(obs.board) + H_o + hb * m

    def _carry(self, obs, r, f):
        """Move a fair value of theirs, as of round r, to now: every card turned
        since moves it the way an honest naive/reader fair moves."""
        un = self._unseen_at(obs, r)
        m_me = _avg(un)
        nb = r - 1
        B = sum(obs.board[:nb])
        H_o = f - B - (10 - nb) * m_me                 # their hand, read at face value
        nd = sum(1 for rr, w, c in obs.discards if rr <= r)
        D = sum(c for rr, w, c in obs.discards if rr <= r)
        N = 47 - nb - nd
        U = DECK - H_o - B - D
        k = 10 - nb
        for i in range(nb, len(obs.board)):
            c = obs.board[i]
            mo = U / N
            f += (c - mo) * (N - k) / (N - 1)
            U -= c
            N -= 1
            k -= 1
        for rr, w, c in obs.discards:
            if rr > r:
                mo = U / N
                if w == "me":
                    f += k * (mo - c) / (N - 1)
                else:
                    f += _avg(obs.unseen) - c
                U -= c
                N -= 1
        return f

    def pred_opp(self, obs):
        """Their fair now: their last quote carried forward, then (TB) kept
        inside what their trades on my quotes prove: a buy at x + 2 means
        their fair was above x + 2 + TB_G, a sell below x - 2 - TB_G."""
        oq = self._opp_quotes(obs)
        if not oq:
            return None
        r, q = oq[-1]
        f = self._carry(obs, r, q)
        if self.P["TB"]:
            lo, hi = -1e9, 1e9
            for rr, w, px, n in obs.tape:
                if w == "me" and n > 0:
                    lo = max(lo, self._carry(obs, rr, px + 2 + self.P["TB_G"]))
                elif w == "me" and n < 0:
                    hi = min(hi, self._carry(obs, rr, px - 2 - self.P["TB_G"]))
            if lo <= hi:
                f = min(hi, max(lo, f))
            else:
                f = (lo + hi) / 2
        return f

    def pub(self, obs):
        left = [4] * 13
        for c in obs.board:
            left[c - 1] -= 1
        for _, _, c in obs.discards:
            left[c - 1] -= 1
        return sum(obs.board) + (15 - len(obs.board)) * _avg(left)

    def naive_fair(self, obs):
        m = _avg(obs.unseen)
        return sum(obs.hand) + sum(obs.board) + (10 - len(obs.board)) * m

    # ------------------------------------------------------------ actions
    def move(self, obs):
        self._track(obs)
        if any(w == "me" for _, w, _ in obs.discards):
            return None
        p = self.P
        pos = obs.position
        if pos == 0 and not (p["SWAP"] == "round" and p["SWAP_FLAT"] and obs.round >= p["SWAP_R"]):
            return None
        m = _avg(obs.unseen)
        h = obs.hand
        lo = min(range(5), key=lambda i: h[i])
        hi = max(range(5), key=lambda i: h[i])
        if pos == 0:
            i = max(range(5), key=lambda j: abs(h[j] - m))
            gain = abs(h[i] - m)
        else:
            i = lo if pos > 0 else hi
            gain = (m - h[i]) if pos > 0 else (h[i] - m)
        rule = p["SWAP"]
        if rule == "sharp":
            ok = gain > 3
        elif rule == "r5":
            ok = obs.round == 5 and gain > 0
        elif rule == "r5pos3":
            ok = obs.round == 5 and gain > 0 and abs(pos) >= 3
        elif rule == "round":
            ok = obs.round >= p["SWAP_R"] and gain > p["SWAP_G"]
        else:
            ok = False
        if ok:
            return ("SWAP", i)
        return None

    def quote(self, obs):
        self._track(obs)
        p = self.P
        P = self.pred_opp(obs)
        if P is None:
            if p["R1_QUOTE"] == "pub":
                return round(self.pub(obs) + p["R1_ADD"], 2)
            return round(self.naive_fair(obs) + p["R1_ADD"], 2)
        if p["MIRROR"]:
            return round(self._opp_quotes(obs)[-1][1], 2)
        F = self.fair(obs)
        m = _avg(obs.unseen)
        F -= p["HIDE"] * (sum(obs.hand) - 5 * m)
        x = (1 - p["W"]) * (F - p["SKEW_Q"] * obs.position) + p["W"] * P + p["C_Q"]
        pos = obs.position
        if p["AGGRO_K"] and abs(pos) < p["AGGRO_LIM"]:
            d = (1 if pos > 0 else -1) if pos else (1 if F > P else -1)
            x = P + d * p["AGGRO_K"]
        if p["SNAP"] is not None and abs(x - P) > p["SNAP_IN"]:
            x = P + (p["SNAP"] if x > P else -p["SNAP"])
        return round(min(195.0, max(0.0, x)), 2)

    def respond(self, obs, price):
        self._track(obs)
        p = self.P
        e = self.fair(obs, price) - p["SKEW_R"] * obs.position - price
        a = abs(e)
        n = 2 if a > p["TH2"] else (1 if a > p["TH1"] else 0)
        if obs.round == 1:
            n = min(n, p["R1_MAXLOT"])
        return n if e > 0 else -n
