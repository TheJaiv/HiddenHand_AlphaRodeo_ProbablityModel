# Team Name: Field model - KRYPTEX
# Members: none (local imitation, never uploaded)
# Mentor: none
"""opp_kryptex.py - avengers imitation of live team KRYPTEX #512, fitted to public replays (avengers/refit.py seed 3), loss 4.183.
Same opp_core as heist/opp_core.py."""

"""heist/opp_core.py - one parameterised bot that can imitate the styles seen on the live arena.

Used by heist/fit_opp.py (fits P to a team's public replays and live scores) and copied into
every heist/opp_<team>.py (self-contained: core + that team's P). Never uploaded.

Its value estimate E (stateless, recomputed from obs at every call):
    naive card count (hand + board + peeked + unknowns x unseen average)
  + T  x (what the opponent's last quote implies about its hand - average hand)   [reader]
         (quotes further than SANE from the public estimate are not read)
  + TL x (lots the opponent bought on my quotes - lots it sold)                   [trade learning]
  + SA x sum(m - card) over the opponent's discards                                [swap accounting]
Quote:   first quote of the deal: (1-H1)*E + H1*public + FQ
         later: W*(their last quote, carried for board cards, + C*s) + (1-W)*((1-HIDE)*E + HIDE*public) + QA
                s = sign(E - their last quote) if CSIGN else +1;   minus SKEW * position
Respond: edge = E (reading the price too if TP, with trust TR) - price; |edge| > TH -> 1 lot, > TH2 -> 2 lots,
         at most R1L lots in round 1; ASYM shifts the edge (buy more readily than sell); a price further than SANR from the public estimate is ignored.
Move:    one swap from round RS on: lowest card when long (or flat and E > public), highest when short,
         if the card is at least SG from the unseen average. PK: peek in round PK (0 = never); PKN: peek in every round up to PKN.
"""

DEFAULT = dict(FQ=0.0, H1=0.0, T=0.0, SANE=99.0, TL=0.0, SA=0.0, W=0.0, C=0.0, CSIGN=1, HIDE=0.0,
               QA=0.0, SKEW=0.0, TP=0, TR=0.0, TH=2.0, TH2=3.0, ASYM=0.0, R1L=2, SANR=999.0, RS=1, SG=3.0, PK=0, PKN=0)


def make_bot(P):
    P = dict(DEFAULT, **P)

    class Bot:
        @staticmethod
        def _m(obs):
            n = sum(obs.unseen)
            return sum((r + 1) * c for r, c in enumerate(obs.unseen)) / n if n else 7.0

        @staticmethod
        def _public(obs):
            """What an average hand on both sides implies, from public cards only."""
            u = [4] * 13
            for k in obs.board:
                u[k - 1] -= 1
            for _, _, k in obs.discards:
                u[k - 1] -= 1
            n = sum(u)
            mp = sum((r + 1) * c for r, c in enumerate(u)) / n
            return sum(obs.board) + (15 - len(obs.board)) * mp

        def _est(self, obs, price=None):
            m = self._m(obs)
            nb = len(obs.board)
            nk = len(obs.opp_known)
            E = sum(obs.hand) + sum(obs.board) + sum(obs.opp_known) + (10 - nb - nk) * m
            pub = self._public(obs)
            theirs = [px for r, who, px, q in obs.tape if who == "opp"]
            T = P["T"]
            if P["TP"] and price is not None:
                theirs.append(price)
                T = P["TR"]
            if theirs and T:
                last = theirs[-1]
                if abs(last - pub) <= P["SANE"]:
                    implied = last - sum(obs.board) - (5 + 5 - nb) * m
                    E += T * (implied - 5 * m)
            if P["TL"]:
                net = sum(q for r, who, px, q in obs.tape if who == "me")
                E += P["TL"] * net
            if P["SA"]:
                E += P["SA"] * sum(m - k for r, who, k in obs.discards if who == "opp")
            return E, pub

        def move(self, obs):
            if P["PK"] and obs.round == P["PK"] and not any(w == "me" for _, w in obs.peeks):
                return "PEEK"
            if obs.round <= P["PKN"]:
                return "PEEK"
            if obs.round < P["RS"] or any(w == "me" for _, w, _ in obs.discards):
                return None
            E, pub = self._est(obs)
            m = self._m(obs)
            h = obs.hand
            lo = min(range(5), key=lambda i: h[i])
            hi = max(range(5), key=lambda i: h[i])
            long_ = obs.position > 0 or (obs.position == 0 and E > pub)
            if long_ and m - h[lo] >= P["SG"]:
                return ("SWAP", lo)
            if not long_ and h[hi] - m >= P["SG"]:
                return ("SWAP", hi)
            return None

        def quote(self, obs):
            E, pub = self._est(obs)
            last = None
            for r, who, px, q in obs.tape:
                if who == "opp":
                    last = (r, px)
            if last is not None and abs(last[1] - pub) > P["SANR"]:
                last = None
            if last is None:
                q = (1 - P["H1"]) * E + P["H1"] * pub + P["FQ"]
            else:
                rq, lq = last
                for c in obs.board[rq - 1:obs.round - 1]:
                    lq += c - 7.0
                s = (1 if E >= lq else -1) if P["CSIGN"] else 1
                hq = (1 - P["HIDE"]) * E + P["HIDE"] * pub
                q = P["W"] * (lq + P["C"] * s) + (1 - P["W"]) * hq + P["QA"]
            q -= P["SKEW"] * obs.position
            return min(195.0, max(0.0, q))

        def respond(self, obs, price):
            E, pub = self._est(obs, price)
            if abs(price - pub) > P["SANR"]:
                return 0
            e = E - price + P["ASYM"]          # ASYM > 0: buys more readily than it sells
            n = 2 if abs(e) > P["TH2"] else (1 if abs(e) > P["TH"] else 0)
            if obs.round == 1:
                n = min(n, P["R1L"])
            return n if e > 0 else -n

    return Bot


Bot = make_bot({"FQ": 1.6034428999618604, "H1": 0.22406033179798682, "T": 0.6006631665368791, "SANE": 16.516282438004858, "TL": -0.09932794614040913, "SA": 0.46394798388297365, "W": 0.6921744846674165, "C": 1.100756695045192, "CSIGN": 1, "HIDE": 0.4856400021525935, "QA": 0.7461554678489086, "SKEW": 0.4074508741313476, "TP": 1, "TR": 0.6186550191507769, "TH": 6.207686583862375, "TH2": 6.207686583862375, "ASYM": -4.087277539562894, "R1L": 2, "SANR": 91.14276827186782, "RS": 1, "SG": 2.13501636300087})
