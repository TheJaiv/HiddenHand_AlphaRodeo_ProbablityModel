"""field_fit.py - per team, regress its quotes (minus its naive fair) on what our last quote implies.
x = quote - naive_fair_own ; y1 = implied hand from opp's last quote - 5m ; y2 = own hand - 5m
reader: x ~ 0.8*y1 ; blend: x ~ W*(y1 - y2) ; hider: x ~ -h*y2 ; naive: x ~ 0"""
import json, glob, collections, sys, statistics as st
RK = {'A': 1, 'J': 11, 'Q': 12, 'K': 13}
def rk(s):
    s = s[:-1]
    return RK.get(s) or int(s)
fl = json.load(open('versions/hunt_scratch_B/fights.json'))
cur = {}
for x in fl:
    for me, mid, ot, oid in ((x['a'], x['a_id'], x['b'], x['b_id']), (x['b'], x['b_id'], x['a'], x['a_id'])):
        if me == 'Alpha Rodeo' and mid == 448:
            cur[ot] = oid
rows = collections.defaultdict(list)
first_q = collections.defaultdict(list)
for f in glob.glob('zoo/arena_raw/*/*.json'):
    d = json.load(open(f))
    if not isinstance(d, dict):
        continue
    ids = d.get('entry_ids', {})
    for p in d['plays']:
        for i in (0, 1):
            team = p['seats'][i]
            key = (team, ids.get(team))
            hand = list(p['hand_ranks'][i])
            board = p['board_ranks']
            disc = []
            opp_last = None
            for row in p['rounds']:
                r = row['round']
                for j, mv in enumerate(row['moves']):
                    if mv and mv.get('kind') == 'swap':
                        disc.append(rk(mv['out']))
                        if j == i:
                            hand.remove(rk(mv['out']))
                            hand.append(rk(mv['in']))
                shown = board[:r - 1]
                unseen = [4] * 13
                for c in hand + shown + disc:
                    unseen[c - 1] -= 1
                U = sum(unseen)
                m = sum((k + 1) * c for k, c in enumerate(unseen)) / U
                nb = len(shown)
                for q in row['quotes']:
                    if q['maker'] == i:
                        naive = sum(hand) + sum(shown) + (10 - nb) * m
                        x = q['price'] - naive
                        if opp_last is None:
                            first_q[key].append(x)
                        else:
                            imp = opp_last - sum(shown) - (10 - nb) * m
                            rows[key].append((x, imp - 5 * m, sum(hand) - 5 * m, r))
                    else:
                        opp_last = q['price']
def ols(data):
    # x = a + b1*y1 + b2*y2
    n = len(data)
    X = [(1.0, y1, y2) for _, y1, y2, _ in data]
    Y = [x for x, *_ in data]
    A = [[sum(X[k][i] * X[k][j] for k in range(n)) for j in range(3)] for i in range(3)]
    B = [sum(X[k][i] * Y[k] for k in range(n)) for i in range(3)]
    # solve 3x3
    import copy
    M = [A[i] + [B[i]] for i in range(3)]
    for c in range(3):
        piv = max(range(c, 3), key=lambda r: abs(M[r][c]))
        M[c], M[piv] = M[piv], M[c]
        if abs(M[c][c]) < 1e-9:
            return None
        for r in range(3):
            if r != c:
                fct = M[r][c] / M[c][c]
                M[r] = [a - fct * b for a, b in zip(M[r], M[c])]
    sol = [M[i][3] / M[i][i] for i in range(3)]
    res = [Y[k] - sum(s * xx for s, xx in zip(sol, X[k])) for k in range(n)]
    return sol, (sum(e * e for e in res) / max(1, n - 3)) ** .5
print(f"{'team':<24}{'entry':>6}{'n':>5}  {'a':>6} {'b1(our q)':>9} {'b2(own)':>8} {'resid':>6}  first-quote offset")
for t, i in sorted(cur.items()):
    key = (t, i)
    tag = ''
    if key not in rows:
        alts = [k for k in rows if k[0] == t]
        if not alts:
            print(f"{t:<24}{i:>6}  no replays"); continue
        key = max(alts, key=lambda k: k[1] or 0); tag = f'(old #{key[1]})'
    data = rows[key]
    fit = ols(data) if len(data) > 6 else None
    fq = st.mean(first_q[key]) if first_q[key] else float('nan')
    if fit:
        (a, b1, b2), s = fit
        print(f"{t:<24}{i:>6}{len(data):>5}  {a:+6.2f} {b1:+9.2f} {b2:+8.2f} {s:6.2f}  {fq:+.2f} {tag}")
    else:
        print(f"{t:<24}{i:>6}{len(data):>5}  too few {tag}")
