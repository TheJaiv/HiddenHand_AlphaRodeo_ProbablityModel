# Team Name: Zoo - arena_quantumlesssss
# Members: Organisers
# Mentor: None

"""
arena_quantumlesssss.py - imitation of arena team "Quantumlesssss" (entry #29, v3),
decoded from its public replays (zoo/arena_raw/quantumlesssss/). Quantumlesssss
beat Alpha Rodeo in all 5 of their arena fights (every entry of both).

What the replays show, and what this file does:

  * First quote of the deal (no opponent quote yet): the PUBLIC estimate,
    105.00 at the start, whatever its hand. Its hand does not show.
  * Every later quote is a blend of its own value F and P, its prediction
    of the opponent's fair:
        quote = (1 - W) * (F - SKEW_Q * position) + W * P + C_Q
    Exact in the replays for its first quote as second maker:
        0.636 * own naive fair + 0.364 * their quote - 0.44 - 1.46 * position
    (9 different opponent quotes, all within 0.07). Against the house bots
    its quotes often land just past their +-2 band (-2.11, +2.09, -2.51 vs
    naive), so the opponent trades with it at the edge of its range.
  * P believes their TRADES over their quotes. P starts from their last
    quote (moved for each card turned since) but is then kept inside what
    their trades on its quotes prove: a buy at x + 2 means their fair was
    above x + 2, a sell at x - 2 means below (TB). Against rival_3, which
    quotes against its hand to steer readers: rival_3 quoted 110.58 right
    after selling to it at 104.12, and Quantumlesssss quoted 102.16
    (= 104.12 - 1.96); rival_3 sold to it again.
  * Its value F: their last AVG_Q quotes read with trust T, moved half way
    (TB_F) to the hand that the trade-bounded P implies, plus TRADE_EV per
    lot they bought from it (minus per lot sold). Without the trade terms
    the copy LOST to rival_3 (-2.0 instead of the arena's +1.2).
  * As taker it reads the price it is answering, skews its value against
    its position (SKEW_R per lot) and only trades on a large edge (TH1/TH2).
  * Swap: round 5 only, whenever it holds a position (lowest card when long,
    highest when short: 64 of 66 plays;
    the other 2 were flat). Never peeks.

P and F are rebuilt from obs on every call; the only memory is which card
our own swap brought in. Parameters were fitted to its replays (quote and
response agreement) and to its arena scores against naive, reader, sharp
and rival_3.
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
        R1_ADD=0.0,         # added to that first quote
        W=0.346,            # quote = (1-W)*(F - SKEW_Q*pos) + W*P + C_Q
        SKEW_Q=2.085,       # quote: my value moves this much against each lot I hold
        C_Q=-0.18,          # quote: constant offset
        HIDE=-0.098,        # subtract HIDE * (my hand - 5m) from the quote
        SNAP=None,          # if set: |quote - P| beyond SNAP_IN -> P +- SNAP (trade at the band edge)
        SNAP_IN=1.95,       # ... (unused when SNAP is None)
        SKEW_R=2.128,       # respond: fair - SKEW_R*pos
        TH1=4.35,           # respond: 1 lot if edge > TH1
        TH2=5.624,          # respond: 2 lots if edge > TH2
        R1_MAXLOT=2,        # most lots it takes in round 1
        SWAP='r5',          # "sharp" (any round, card beyond m +- 3), "r5", "r5pos3"
        AVG_Q=2,            # average the hand read from their last AVG_Q quotes
        TRADE_EV=1.475,     # their hand estimate moves this much per lot they bought (+) / sold (-) on my quotes
        AGGRO_K=0.0,        # if set: quote = P + d*AGGRO_K, d = side of my position (or of F - P when flat)
        AGGRO_LIM=10,       # ... while |position| < AGGRO_LIM
        TB=1,               # 1: their trades on my quotes bound their predicted fair P
        TB_G=-0.127,        # ... margin past the traded price
        TB_F=0.5,           # weight of "their hand read from the bounded P" in my value F
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
        if pos == 0:
            return None
        m = _avg(obs.unseen)
        h = obs.hand
        lo = min(range(5), key=lambda i: h[i])
        hi = max(range(5), key=lambda i: h[i])
        i = lo if pos > 0 else hi
        gain = (m - h[i]) if pos > 0 else (h[i] - m)
        rule = p["SWAP"]
        if rule == "sharp":
            ok = gain > 3
        elif rule == "r5":
            ok = obs.round == 5 and gain > 0
        elif rule == "r5pos3":
            ok = obs.round == 5 and gain > 0 and abs(pos) >= 3
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
