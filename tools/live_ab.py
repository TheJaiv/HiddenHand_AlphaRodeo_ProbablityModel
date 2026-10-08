"""
tools/live_ab.py - compare our live uploads on the SAME opponents (local only)
==============================================================================

One polite GET of the public fight list (https://hiddenhand.tqciitbhu.org/fights),
then, for our team:

    python tools/live_ab.py                 every upload: fights, mean score, wins
    python tools/live_ab.py 368             newest upload vs entry #368 on shared opponents
    python tools/live_ab.py 368 401         entry #401 vs entry #368 on shared opponents

"Shared" means the same opponent upload (same entry id), so the comparison is paired:
the opponent bot is identical, only ours differs. The +-2se is over those pairs.
Each live fight is 400 deals, so one fight's score is good to about +-0.7.
"""

from __future__ import annotations

import html
import re
import subprocess
import sys

URL = "https://hiddenhand.tqciitbhu.org/fights"
TEAM = "Alpha Rodeo"


def fetch() -> list[dict]:
    t = subprocess.run(["curl", "-sf", "-A", "Mozilla/5.0", URL], capture_output=True, check=True).stdout.decode()
    out = []
    for tr in re.findall(r"<tr>(.*?)</tr>", t, re.S):
        if "/match/" not in tr:
            continue
        td = [html.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        a, b = (re.match(r"(.*) #(\d+)$", s) for s in (td[2], td[4]))
        if a and b:
            out.append({"when": td[0], "a": a.group(1), "a_id": int(a.group(2)), "sa": float(td[3]),
                        "b": b.group(1), "b_id": int(b.group(2)), "sb": float(td[5])})
    return out


def ours(fights: list[dict]) -> dict:
    """entry id -> {(opponent, opponent entry): our score}"""
    res: dict[int, dict] = {}
    for f in fights:
        for me, opp in (("a", "b"), ("b", "a")):
            if f[me] == TEAM:
                res.setdefault(f[me + "_id"], {})[(f[opp], f[opp + "_id"])] = f["s" + me]
    return res


def main() -> int:
    res = ours(fetch())
    if not res:
        sys.exit(f"no fights of {TEAM} found")
    print(f"{TEAM} uploads (entry id: fights, mean score, wins)")
    for e in sorted(res):
        v = list(res[e].values())
        print(f"  #{e:<5} {len(v):3d} fights  mean {sum(v) / len(v):+6.2f}  wins {sum(x > 0 for x in v)}")
    if len(sys.argv) < 2:
        return 0
    ref = int(sys.argv[1])
    new = int(sys.argv[2]) if len(sys.argv) > 2 else max(res)
    shared = sorted(set(res.get(ref, {})) & set(res.get(new, {})), key=lambda k: res[new][k] - res[ref][k])
    if not shared:
        print(f"\nno shared opponents yet between #{new} and #{ref}")
        return 0
    d = [res[new][k] - res[ref][k] for k in shared]
    m = sum(d) / len(d)
    se = (sum((x - m) ** 2 for x in d) / (len(d) - 1)) ** 0.5 / len(d) ** 0.5 if len(d) > 1 else float("nan")
    print(f"\n#{new} - #{ref} on {len(d)} shared opponent uploads: mean {m:+.2f}  +-2se {2 * se:.2f}")
    for k, x in zip(shared, d):
        print(f"  {k[0]:<22}#{k[1]:<5} #{new} {res[new][k]:+6.2f}   #{ref} {res[ref][k]:+6.2f}   diff {x:+6.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
