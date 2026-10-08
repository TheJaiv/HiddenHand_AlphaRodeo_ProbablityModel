# Team Name: Field model - Genz7 sf35
# Members: none (local imitation, never uploaded)
# Mentor: none
"""opp_genz7_sf35.py - imitation of live team Genz7 sf35 #262, fitted to its public replays
(heist/fit_opp.py): quote err 3.02, respond miss 0.53, move miss 0.02.
See heist/opp_core.py for what the parameters mean."""


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


Bot = make_bot({"FQ": 2.4216, "H1": 0.3728, "T": 0.2055, "SANE": 17.527, "TL": 0.5449, "SA": 0.1226, "W": 0.7513, "C": -2.8167, "CSIGN": 0, "HIDE": 0.5272, "QA": 2.3952, "SKEW": 0.9072, "TP": 1, "TR": 0.5379, "TH": 4.0137, "TH2": 9.0, "R1L": 2, "SANR": 60.9396, "RS": 5, "SG": 0.1522})
