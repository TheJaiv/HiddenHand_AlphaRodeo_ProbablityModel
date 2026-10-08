"""Print a team's decisions next to reference fair values.

    python show.py TEAM_DIR "Team Name" ENTRY [seat]
  nf  = naive fair: hand + board + unknown cards x avg unseen
  sf  = sharp fair (TRUST 0.8 on opp's last quote)
  pub = public estimate (board + rest at public avg; hider's quote)
"""
import sys

import tapes


def avg(o):
    return sum((r + 1) * c for r, c in enumerate(o.unseen)) / sum(o.unseen)


def nf(o):
    m = avg(o)
    return sum(o.hand) + sum(o.board) + sum(o.opp_known) + (10 - len(o.board) - len(o.opp_known)) * m


def sf(o, trust=0.8):
    m = avg(o)
    hb = 5 - len(o.board)
    oh = sum(o.opp_known) + (5 - len(o.opp_known)) * m
    th = [px for r, w, px, q in o.tape if w == "opp"]
    if th:
        implied = th[-1] - sum(o.board) - (5 + hb) * m
        oh += trust * (implied - oh)
    return sum(o.hand) + sum(o.board) + oh + hb * m


def pub(o):
    left = [4] * 13
    for r in o.board:
        left[r - 1] -= 1
    for _, _, r in o.discards:
        left[r - 1] -= 1
    pa = sum((r + 1) * c for r, c in enumerate(left)) / sum(left)
    return sum(o.board) + (15 - len(o.board)) * pa


def main():
    team_dir, team, entry = sys.argv[1], sys.argv[2], int(sys.argv[3])
    seat = int(sys.argv[4]) if len(sys.argv) > 4 else None
    cur = None
    for kind, o, act, ex in tapes.team_decisions(team_dir, team, entry):
        if seat is not None and ex["seat"] != seat:
            continue
        key = (ex["fight"], ex["seat"])
        if key != cur:
            cur = key
            print(f"\n== {ex['fight']}  seat{ex['seat']} vs {ex['opp']}  hand {o.hand}")
        r = ex["round"]
        base = f"r{r} pos{o.position:+3d} nf={nf(o):6.2f} sf={sf(o):6.2f} pub={pub(o):6.2f}"
        if kind == "move":
            if act is not None:
                print(f"  r{r} MOVE {act}  hand {o.hand} pos {o.position} board {o.board}")
        elif kind == "quote":
            print(f"  {base}  QUOTE {act}   q-nf={act - nf(o):+6.2f} q-sf={act - sf(o):+6.2f} q-pub={act - pub(o):+6.2f}")
        else:
            p = ex["price"]
            print(f"  {base}  RESP {act:+d} @ {p:7.2f}  nf-p={nf(o) - p:+6.2f} sf-p={sf(o) - p:+6.2f}")


if __name__ == "__main__":
    main()
