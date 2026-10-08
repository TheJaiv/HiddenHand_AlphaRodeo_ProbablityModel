"""Read-only scraper for the Hidden Hand arena: fight list + fight pages -> JSON.

    python scrape.py list                      -> fights.json (every fight on /fights)
    python scrape.py fight /match/live/15/29   -> prints parsed JSON
    python scrape.py team "Quantumlesssss" OUT_DIR [--all-entries]
"""
import html as H
import json
import os
import re
import sys
import subprocess
import time

BASE = "https://hiddenhand.tqciitbhu.org"
UA = {"User-Agent": "Mozilla/5.0"}
RANK = {"A": 1, "J": 11, "Q": 12, "K": 13}
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "html")


def get(path):
    os.makedirs(CACHE, exist_ok=True)
    fn = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9]+", "_", path.strip("/")) + ".html")
    if os.path.exists(fn) and path != "/fights":
        return open(fn, encoding="utf-8").read()
    t = subprocess.run(["curl", "-sf", "-A", UA["User-Agent"], BASE + path],
                       capture_output=True, check=True).stdout.decode("utf-8")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(t)
    time.sleep(1.1)
    return t


def strip(s):
    return H.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def card_rank(c):
    c = c.strip()
    v = c[:-1]
    return RANK.get(v) or int(v)


def cards(s):
    return [strip(x) for x in re.findall(r'<span class="c[^"]*">(.*?)</span>', s)]


def parse_fights(t):
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
        out.append({"when": tds[0], "stage": tds[1], "a": a, "a_id": ai, "score_a": float(tds[3]),
                    "b": b, "b_id": bi, "score_b": float(tds[5]), "href": m.group(1)})
    return out


TRADE = re.compile(r"^(.*?) quotes ([\d.]+)( \(no valid quote, house price\)| no quote)?; (.*?) "
                   r"(passes|buys (\d+) at ([\d.]+)|sells (\d+) at ([\d.]+))$")


def parse_play(sec, names_hint):
    """One 'Deal 1, ...' section."""
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
            m = re.match(r"(.*?) peeks and sees (\S+)$", txt)
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
            if m.group(6):
                qty = int(m.group(6))
            elif m.group(8):
                qty = -int(m.group(8))
            else:
                qty = 0
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
    title = strip(re.search(r"<h1>(.*?)</h1>", t, re.S).group(1))
    lede = strip(re.search(r'<p class="lede">(.*?)</p>', t, re.S).group(1))
    m = re.search(r"(\d+) deals\.\s*(.*?) score ([+-][\d.]+) \(([+-][\d.]+) PnL per deal\),\s*(.*?) score "
                  r"([+-][\d.]+) \(([+-][\d.]+) PnL per deal\)", lede, re.S)
    secs = re.split(r"<h2>", t)[1:]
    plays = [parse_play(s, None) for s in secs if s.startswith("Deal")]
    return {"href": href, "title": title, "deals": int(m.group(1)),
            "a": m.group(2).strip(), "score_a": float(m.group(3)), "pnl_a": float(m.group(4)),
            "b": m.group(5).strip(), "score_b": float(m.group(6)), "pnl_b": float(m.group(7)),
            "plays": plays}


def main():
    cmd = sys.argv[1]
    if cmd == "list":
        fl = parse_fights(get("/fights"))
        json.dump(fl, open(os.path.join(CACHE, "..", "fights.json"), "w"), indent=1, ensure_ascii=False)
        print(len(fl), "fights")
    elif cmd == "fight":
        print(json.dumps(parse_fight(get(sys.argv[2]), sys.argv[2]), indent=1, ensure_ascii=False))
    elif cmd == "team":
        team, out = sys.argv[2], sys.argv[3]
        fl = json.load(open(os.path.join(CACHE, "..", "fights.json")))
        mine = [f for f in fl if team in (f["a"], f["b"])]
        ids = sorted({f["a_id"] if f["a"] == team else f["b_id"] for f in mine})
        want = ids if "--all-entries" in sys.argv else ids[-1:]
        os.makedirs(out, exist_ok=True)
        n = 0
        for f in mine:
            me = f["a_id"] if f["a"] == team else f["b_id"]
            if me not in want:
                continue
            d = parse_fight(get(f["href"]), f["href"])
            d["entry_ids"] = {f["a"]: f["a_id"], f["b"]: f["b_id"]}
            d["when"] = f["when"]
            opp = f["b"] if f["a"] == team else f["a"]
            oid = f["b_id"] if f["a"] == team else f["a_id"]
            fn = f"{me}_vs_{re.sub(r'[^A-Za-z0-9]+', '_', opp)}_{oid}.json"
            json.dump(d, open(os.path.join(out, fn), "w"), indent=1, ensure_ascii=False)
            n += 1
        print(team, "entries", ids, "saved", n, "fights for", want)


if __name__ == "__main__" and sys.argv[1] != "page":
    main()


def team_page(team, out):
    """Current head-to-head of a team (its team page) -> every listed fight saved as JSON."""
    import urllib.parse
    t = get("/team/" + urllib.parse.quote(team))
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", t, re.S):
        m = re.search(r'href="(/match/[^"]+)"', tr)
        if not m:
            continue
        tds = [strip(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        rows.append((tds[0], float(tds[1]), float(tds[2]), m.group(1)))
    os.makedirs(out, exist_ok=True)
    summary = []
    for opp, sc, pnl, href in rows:
        d = parse_fight(get(href), href)
        a_id, b_id = [int(x) for x in href.rstrip("/").split("/")[-2:]]
        d["entry_ids"] = {d["a"]: a_id, d["b"]: b_id}
        me = a_id if d["a"] == team else b_id
        oid = b_id if d["a"] == team else a_id
        fn = f"{me}_vs_{re.sub(r'[^A-Za-z0-9]+', '_', opp)}_{oid}.json"
        json.dump(d, open(os.path.join(out, fn), "w"), indent=1, ensure_ascii=False)
        summary.append({"opp": opp, "opp_id": oid, "me": me, "score": sc, "pnl": pnl})
    json.dump(summary, open(os.path.join(out, f"_headtohead_{summary[0]['me']}.json"), "w"), indent=1, ensure_ascii=False)
    return summary


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "page":
    s = team_page(sys.argv[2], sys.argv[3])
    print(sys.argv[2], "entry", s[0]["me"], "fights", len(s))
