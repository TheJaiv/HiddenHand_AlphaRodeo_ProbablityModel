"""heist/census.py - the live field from the public arena pages (read only, polite).

    python3 -I heist/census.py            fetch standings + fight list (cached 5 min), build heist/data/matrix.json
    python3 -I heist/census.py --cached   rebuild from the newest cached pages, no network

Only plain GETs of public pages (/ and /fights), at most one request per 1.2 s.
Everything fetched is cached under heist/data/html/ with a time stamp.
"""

from __future__ import annotations

import glob
import html as H
import json
import os
import re
import subprocess
import sys
import time

BASE = "https://hiddenhand.tqciitbhu.org"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CACHE = os.path.join(DATA, "html")
TEAM = "Alpha Rodeo"
HOUSE = ("naive", "reader", "sharp")
_last = [0.0]


def get(path: str, name: str, max_age: float = 300.0, cached_only: bool = False) -> str:
    """Newest cached copy of a page if younger than max_age seconds, else one polite GET."""
    os.makedirs(CACHE, exist_ok=True)
    old = sorted(glob.glob(os.path.join(CACHE, f"{name}_*.html")))
    if old and (cached_only or time.time() - os.path.getmtime(old[-1]) < max_age):
        return open(old[-1], encoding="utf-8").read()
    wait = 1.2 - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    t = subprocess.run(["curl", "-sf", "-A", "Mozilla/5.0", BASE + path],
                       capture_output=True, check=True).stdout.decode("utf-8")
    _last[0] = time.time()
    with open(os.path.join(CACHE, f"{name}_{time.strftime('%m%d_%H%M%S')}.html"), "w", encoding="utf-8") as f:
        f.write(t)
    return t


def strip(s: str) -> str:
    return H.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def parse_standings(t: str) -> list[dict]:
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S):
        tds = [strip(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(tds) < 6 or not tds[0].isdigit() and tds[0] not in ("", "-"):
            continue
        try:
            score, pnl = float(tds[2]), float(tds[3])
        except ValueError:
            continue
        won, fought = (int(x) for x in tds[4].split("/")) if "/" in tds[4] else (0, 0)
        out.append({"rank": int(tds[0]) if tds[0].isdigit() else None, "team": tds[1], "score": score,
                    "pnl": pnl, "won": won, "fights": fought, "version": tds[5]})
    return out


def parse_fights(t: str) -> list[dict]:
    out = []
    for tr in re.findall(r"<tr>(.*?)</tr>", t, re.S):
        m = re.search(r'href="(/match/[^"]+)"', tr)
        if not m:
            continue
        tds = [strip(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]

        def ent(s):
            mm = re.match(r"(.*) #(\d+)$", s)
            return (mm.group(1), int(mm.group(2))) if mm else (s, None)

        a, ai = ent(tds[2])
        b, bi = ent(tds[4])
        out.append({"when": tds[0], "stage": tds[1], "a": a, "a_id": ai, "sa": float(tds[3]),
                    "b": b, "b_id": bi, "sb": float(tds[5]), "href": m.group(1)})
    return out


def build(standings: list[dict], fights: list[dict]) -> dict:
    # every entry of every team, with its fights: entry -> {opponent key: score}
    entries: dict[str, dict[int, dict]] = {}
    first_seen: dict[int, str] = {}
    for f in reversed(fights):                       # the list is newest first
        for me, opp in (("a", "b"), ("b", "a")):
            team, eid = f[me], f[me + "_id"]
            key = f"{f[opp]}#{f[opp + '_id']}" if f[opp + "_id"] is not None else f[opp]
            entries.setdefault(team, {}).setdefault(eid if eid is not None else 0, {})[key] = f["s" + me]
            if eid is not None:
                first_seen.setdefault(eid, f["when"])
    newest = {team: max(es) for team, es in entries.items()}
    # matrix of NEWEST entries: matrix[team][opp] = team's score vs opp's newest entry (if they met)
    nkey = {team: (f"{team}#{e}" if e else team) for team, e in newest.items()}
    matrix: dict[str, dict[str, float]] = {}
    for team, e in newest.items():
        row = {}
        for opp, k in nkey.items():
            if opp != team and k in entries[team][e]:
                row[opp] = entries[team][e][k]
        matrix[team] = row
    ours = {str(e): v for e, v in sorted(entries.get(TEAM, {}).items())}
    return {"made": time.strftime("%Y-%m-%d %H:%M"), "standings": standings,
            "newest": newest, "first_seen": {str(k): v for k, v in first_seen.items()},
            "matrix": matrix, "ours": ours,
            "entries": {team: {str(e): v for e, v in es.items()} for team, es in entries.items()}}


def main() -> int:
    cached = "--cached" in sys.argv
    st = parse_standings(get("/", "standings", cached_only=cached))
    fl = parse_fights(get("/fights", "fights", cached_only=cached))
    m = build(st, fl)
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "matrix.json"), "w", encoding="utf-8") as f:
        json.dump(m, f, indent=1, ensure_ascii=False)
    with open(os.path.join(DATA, "fights.json"), "w", encoding="utf-8") as f:
        json.dump(fl, f, ensure_ascii=False)
    print(f"{len(st)} standings rows, {len(fl)} fights, {len(m['newest'])} teams; our entries: "
          f"{' '.join('#' + e for e in m['ours'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
