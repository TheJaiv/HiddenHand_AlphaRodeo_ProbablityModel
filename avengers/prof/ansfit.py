"""avengers/prof/ansfit.py - how a team answers quotes: their qty vs candidate 'fair - price' models.

    python3 -I avengers/prof/ansfit.py TEAM ENTRY

Builds each candidate fair model F(S,B,h,P,Qcum,pos) from linfit-style coefficients (given on
the command line or a small builtin set), then for every answer event reports the distribution
of edge = F - price conditional on their qty, plus the fraction taken / mean |qty|.
"""
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "heist", "data", "fights")
RANK = {"A": 1, "J": 11, "Q": 12, "K": 13}


def rk(c):
    v = c.strip()[:-1]
    return RANK.get(v) or int(v)


def events(team, entry):
    out = []
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
            mylast = None
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
                            mylast = q["price"]
                    else:
                        S = sum(hands[i])
                        B = sum(board[:shown])
                        h = 5 - shown
                        out.append({"r": r, "S": S, "B": B, "h": h, "P": q["price"],
                                    "Qcum": qcum, "pos": pos[i], "mylast": mylast,
                                    "qty": q["qty"], "their_pos_after": pos[i] + q["qty"]})
                        if q["qty"]:
                            qcum += q["qty"]
                    if q["qty"]:
                        pos[tk] += q["qty"]
                        pos[mk] -= q["qty"]
    return out


MODELS = {
    "cyber": ("a + b*S + c*B + d*P + e*Qcum + f*pos",
              lambda S, B, h, P, Qc, pos, ml: 72.668 - 0.123 * S + 0.225 * B + 0.331 * P + 1.324 * Qc - 1.089 * pos),
    "cyber_mylast": ("a + b*S + c*B + d*mylast + e*Qcum",
                     lambda S, B, h, P, Qc, pos, ml: 60.0 + 0.1 * S + 0.2 * B + 0.55 * (ml or 105.0) + 1.3 * Qc),
    "godtier": ("a + b*S + c*B + d*P + e*Qcum + f*pos",
                lambda S, B, h, P, Qc, pos, ml: 48.415 + 0.485 * S + 0.199 * B + 0.371 * P + 0.346 * Qc - 1.135 * pos),
    "qt": ("-5.8 + 0.03*S + 0.13*B + 1.03*P",
           lambda S, B, h, P, Qc, pos, ml: -5.8 + 0.03 * S + 0.13 * B + 1.03 * P),
    "qt_pure": ("P only", lambda S, B, h, P, Qc, pos, ml: P),
    "qt_Pplus5": ("P + 5", lambda S, B, h, P, Qc, pos, ml: P + 5.0),
    "cyber_P": ("P only", lambda S, B, h, P, Qc, pos, ml: P),
    "cyber_SBP": ("S + B + 5h*7 -> naive fair, then blend with P",
                  lambda S, B, h, P, Qc, pos, ml: S + B + h * 7 + 0.4 * (P - (S + B + h * 7))),
}


def main():
    team, entry = sys.argv[1], int(sys.argv[2])
    ev = events(team, entry)
    print(f"{team} #{entry}: {len(ev)} answer events")
    for name, (desc, f) in MODELS.items():
        rows = {2: [], 1: [], 0: [], -1: [], -2: []}
        for e in ev:
            fair = f(e["S"], e["B"], e["h"], e["P"], e["Qcum"], e["pos"], e["mylast"])
            rows[e["qty"]].append(fair - e["P"])
        print(f"  model {name}: {desc}")
        for k in (2, 1, 0, -1, -2):
            if rows[k]:
                print(f"    qty {k:+d} (n {len(rows[k]):3d}): edge mean {statistics.mean(rows[k]):+7.2f} "
                      f"sd {statistics.pstdev(rows[k]):5.2f}  min {min(rows[k]):+7.2f} max {max(rows[k]):+7.2f}")
        # how well does 'buy iff edge > thr' classify?
        best = None
        for thr in [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]:
            err = sum(1 for e in ev if (f(e["S"], e["B"], e["h"], e["P"], e["Qcum"], e["pos"], e["mylast"]) - e["P"] > thr) != (e["qty"] > 0))
            if best is None or err < best[0]:
                best = (err, thr)
        print(f"    best buy-threshold {best[1]}: mismatches {best[0]}/{len(ev)}")
    # round-1 lot behavior
    r1 = [e for e in ev if e["r"] == 1]
    nz = [e for e in r1 if e["qty"] != 0]
    print(f"  round 1: {len(r1)} answers, {len(nz)} nonzero; qty2 {sum(1 for e in r1 if e['qty']==2)}, "
          f"qty1 {sum(1 for e in r1 if e['qty']==1)}, qty-1 {sum(1 for e in r1 if e['qty']==-1)}, qty-2 {sum(1 for e in r1 if e['qty']==-2)}")
    allnz = [e for e in ev if e["qty"] != 0]
    print(f"  all rounds nonzero: {len(allnz)}/{len(ev)}; |qty|=1: {sum(1 for e in allnz if abs(e['qty'])==1)}, |qty|=2: {sum(1 for e in allnz if abs(e['qty'])==2)}")


if __name__ == "__main__":
    main()
