"""avengers/prof/linfit.py - least-squares models of a team's quoting rule from all its deal-1 replays.

    python3 -I avengers/prof/linfit.py TEAM ENTRY

For every quote event of the team, records features: their hand sum S, board shown sum B,
hidden board count h, opp's last quote P (or 0/none), opp cumulative qty Q, their pos.
Fits several linear structures by least squares and prints coefficients + residual sd.
Also fits their answer rule: their qty vs (model fair - price) threshold.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "heist", "data", "fights")
RANK = {"A": 1, "J": 11, "Q": 12, "K": 13}


def rk(c):
    v = c.strip()[:-1]
    return RANK.get(v) or int(v)


def main():
    team, entry = sys.argv[1], int(sys.argv[2])
    Q = []   # (S, B, h, P, Qcum, pos, quote)
    A = []   # (model_fair_S etc for answers) -> build later
    for fn in sorted(os.listdir(DATA)):
        d = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
        ids = {d["a"]: d["a_id"], d["b"]: d["b_id"]}
        if ids.get(team) != entry:
            continue
        for p in d["plays"]:
            i = p["seats"].index(team)
            hands = [list(map(rk, p["hands"][0])), list(map(rk, p["hands"][1]))]
            board = list(map(rk, p["board"]))
            pos = [0, 0]
            qcum = 0
            lastP = None
            for row in p["rounds"]:
                r = row["round"]
                shown = r - 1
                for s in (0, 1):
                    mv = row["moves"][s]
                    if mv and mv["kind"] == "swap":
                        h = hands[s]
                        h[h.index(rk(mv["out"]))] = rk(mv["in"])
                for q in row["quotes"]:
                    mk, tk = q["maker"], 1 - q["maker"]
                    if mk == i:
                        if not q["auto"]:
                            Q.append((sum(hands[i]), sum(board[:shown]), 5 - shown,
                                      lastP if lastP is not None else None, qcum, pos[i], q["price"]))
                    else:
                        lastP = q["price"]
                        if q["qty"]:
                            qcum += q["qty"]
                    if q["qty"]:
                        pos[tk] += q["qty"]
                        pos[mk] -= q["qty"]
    import statistics
    print(f"{team} #{entry}: {len(Q)} quote events")
    # model 1: quote = a + b*S + c*B + d*P
    for name, use in [
        ("a + b*S", lambda S, B, h, P, Qc, pos: [1.0, S]),
        ("a + b*S + c*B", lambda S, B, h, P, Qc, pos: [1.0, S, B]),
        ("a + b*S + c*B + d*P", lambda S, B, h, P, Qc, pos: [1.0, S, B, P or 105.0]),
        ("a + b*S + c*B + d*P + e*Qcum", lambda S, B, h, P, Qc, pos: [1.0, S, B, P or 105.0, Qc]),
        ("a + b*S + c*B + d*P + e*Qcum + f*pos", lambda S, B, h, P, Qc, pos: [1.0, S, B, P or 105.0, Qc, pos]),
        ("a + b*(S+B) + d*P", lambda S, B, h, P, Qc, pos: [1.0, S + B, P or 105.0]),
        ("a + b*(S+B+h*7) + d*P", lambda S, B, h, P, Qc, pos: [1.0, S + B + h * 7, P or 105.0]),
    ]:
        X = [use(row[0], row[1], row[2], row[3], row[4], row[5]) for row in Q]
        y = [row[6] for row in Q]
        n, m = len(X), len(X[0])
        # normal equations
        XtX = [[sum(X[k][i] * X[k][j] for k in range(n)) for j in range(m)] for i in range(m)]
        Xty = [sum(X[k][i] * y[k] for k in range(n)) for i in range(m)]
        # gauss-jordan
        A_ = [row[:] + [Xty[i]] for i, row in enumerate(XtX)]
        for col in range(m):
            piv = max(range(col, m), key=lambda r: abs(A_[r][col]))
            A_[col], A_[piv] = A_[piv], A_[col]
            for r in range(m):
                if r == col:
                    continue
                f = A_[r][col] / A_[col][col]
                A_[r] = [a - f * b for a, b in zip(A_[r], A_[col])]
        coef = [A_[i][-1] / A_[i][i] for i in range(m)]
        res = [y[k] - sum(coef[j] * X[k][j] for j in range(m)) for k in range(n)]
        sd = statistics.pstdev(res)
        print(f"  {name:<34} coef {[round(c, 3) for c in coef]}  resid sd {sd:.2f}")


if __name__ == "__main__":
    main()
