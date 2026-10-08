"""heist/replays.py - fetch and parse public fight pages (deal 1 replays), politely.

    python3 -I heist/replays.py fight /match/live/452/478        print one parsed fight
    python3 -I heist/replays.py entry 452 [N]                     fetch up to N fights of entry #452
    python3 -I heist/replays.py newest TEAM [N]                   fetch up to N fights of TEAM's newest entry

Pages are cached for good under heist/data/html/match_*.html (a fight never changes);
parsed fights are written to heist/data/fights/<a_id>_<b_id>.json. One GET per 1.2 s at most.
"""

from __future__ import annotations

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
OUT = os.path.join(DATA, "fights")
RANK = {"A": 1, "J": 11, "Q": 12, "K": 13}
_last = [0.0]


def get(path: str) -> str:
    os.makedirs(CACHE, exist_ok=True)
    fn = os.path.join(CACHE, "match_" + re.sub(r"[^A-Za-z0-9]+", "_", path.strip("/")) + ".html")
    if os.path.exists(fn):
        return open(fn, encoding="utf-8").read()
    wait = 1.2 - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    t = subprocess.run(["curl", "-sf", "-A", "Mozilla/5.0", BASE + path],
                       capture_output=True, check=True).stdout.decode("utf-8")
    _last[0] = time.time()
    with open(fn, "w", encoding="utf-8") as f:
        f.write(t)
    return t


def strip(s):
    return H.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def card_rank(c):
    c = c.strip()
    v = c[:-1]
    return RANK.get(v) or int(v)


def cards(s):
    return [strip(x) for x in re.findall(r'<span class="c[^"]*">(.*?)</span>', s)]


TRADE = re.compile(r"^(.*?) quotes ([\d.]+)( \(no valid quote, house price\)| no quote)?; (.*?) "
                   r"(passes|buys (\d+) at ([\d.]+)|sells (\d+) at ([\d.]+))$")


def parse_play(sec):
    panels = re.findall(r'<div class="panel"><b>(.*?)</b>(.*?)</div>', sec, re.S)
    seats = [H.unescape(panels[0][0]), H.unescape(panels[1][0])]
    hands = [cards(panels[0][1]), cards(panels[1][1])]
    board = cards(panels[2][1])
    rounds = []
    body = re.search(r'<table class="deal">.*?<tbody>(.*?)</tbody>', sec, re.S).group(1)
    for tr in re.findall(r"<tr>(.*?)</tr>", body, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        rnd = int(strip(tds[0]))
        moves = [None, None]
        for line in re.split(r"<br\s*/?>", tds[2]):
            txt = strip(line)
            if not txt or txt == "-":
                continue
            m = re.match(r"(.*?) swaps (\S+) → (\S+)$", txt)
            if m:
                moves[seats.index(m.group(1))] = {"kind": "swap", "out": m.group(2), "in": m.group(3)}
                continue
            m = re.match(r"(.*?) peeks(?: and sees|: sees) (\S+)$", txt)
            if m:
                moves[seats.index(m.group(1))] = {"kind": "peek", "card": m.group(2)}
                continue
            m = re.match(r"(.*?) peeks", txt)
            if m:
                moves[seats.index(m.group(1))] = {"kind": "peek", "card": None, "raw": txt}
                continue
            raise ValueError("unknown move: " + txt)
        quotes = []
        for line in re.split(r"<br\s*/?>", tds[3]):
            txt = strip(line)
            if not txt:
                continue
            m = TRADE.match(txt)
            if not m:
                raise ValueError("unknown trade: " + txt)
            maker = seats.index(m.group(1))
            qty = int(m.group(6)) if m.group(6) else (-int(m.group(8)) if m.group(8) else 0)
            quotes.append({"maker": maker, "price": float(m.group(2)), "qty": qty, "auto": bool(m.group(3))})
        rounds.append({"round": rnd, "moves": moves, "quotes": quotes})
    fin = re.search(r"Settles at (\d+)", sec)
    V = int(fin.group(1))
    tail = sec[fin.end():]
    rows = re.findall(r"<tr><td><b>(.*?)</b></td>(.*?)</tr>", tail, re.S)
    final = {}
    for name, rest in rows:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", rest, re.S)
        final[H.unescape(name)] = {"hand": cards(tds[0]), "position": int(strip(tds[1])),
                                   "paid": float(strip(tds[2])), "pnl": float(strip(tds[3]))}
    return {"seats": seats, "hands": hands, "board": board,
            "hand_ranks": [[card_rank(c) for c in h] for h in hands],
            "board_ranks": [card_rank(c) for c in board],
            "rounds": rounds, "V": V,
            "final_hands": [final[s]["hand"] for s in seats],
            "positions": [final[s]["position"] for s in seats],
            "paid": [final[s]["paid"] for s in seats],
            "pnl": [final[s]["pnl"] for s in seats]}


def parse_fight(t, href):
    lede = strip(re.search(r'<p class="lede">(.*?)</p>', t, re.S).group(1))
    m = re.search(r"(\d+) deals\.\s*(.*?) score ([+-][\d.]+) \(([+-][\d.]+) PnL per deal\),\s*(.*?) score "
                  r"([+-][\d.]+) \(([+-][\d.]+) PnL per deal\)", lede, re.S)
    secs = re.split(r"<h2>", t)[1:]
    plays = [parse_play(s) for s in secs if s.startswith("Deal")]
    a_id, b_id = [int(x) for x in href.rstrip("/").split("/")[-2:]]
    return {"href": href, "deals": int(m.group(1)),
            "a": m.group(2).strip(), "score_a": float(m.group(3)), "pnl_a": float(m.group(4)),
            "b": m.group(5).strip(), "score_b": float(m.group(6)), "pnl_b": float(m.group(7)),
            "a_id": a_id, "b_id": b_id, "plays": plays}


def fight(href: str) -> dict:
    a_id, b_id = [int(x) for x in href.rstrip("/").split("/")[-2:]]
    fn = os.path.join(OUT, f"{a_id}_{b_id}.json")
    if os.path.exists(fn):
        return json.load(open(fn, encoding="utf-8"))
    d = parse_fight(get(href), href)
    os.makedirs(OUT, exist_ok=True)
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    return d


def fights_of(entry: int) -> list[dict]:
    fl = json.load(open(os.path.join(DATA, "fights.json"), encoding="utf-8"))
    return [f for f in fl if entry in (f["a_id"], f["b_id"])]


def main() -> int:
    cmd = sys.argv[1]
    if cmd == "fight":
        print(json.dumps(fight(sys.argv[2]), indent=1, ensure_ascii=False))
    elif cmd in ("entry", "newest"):
        if cmd == "entry":
            e = int(sys.argv[2])
        else:
            m = json.load(open(os.path.join(DATA, "matrix.json"), encoding="utf-8"))
            e = m["newest"][sys.argv[2]]
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 9
        fl = fights_of(e)[:n]
        for f in fl:
            fight(f["href"])
        print(f"entry #{e}: {len(fl)} fights cached")
    return 0


if __name__ == "__main__":
    sys.exit(main())
