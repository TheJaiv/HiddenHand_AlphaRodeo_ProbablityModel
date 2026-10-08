"""Fetch our fights (entries 351/368/383/393) vs the target teams into raw_ours/."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scrape
W = os.path.dirname(os.path.abspath(__file__))
fl = json.load(open(os.path.join(W, "fights.json")))
teams = {'TeenPatti': 330, 'Quants Treasure': 377, 'Cyberpsycho': 316, 'PaperHands': 353, 'Genz7': 262, 'AJ_The_Trader': 344}
ours = {351, 368, 383, 393}
out = os.path.join(W, "raw_ours"); os.makedirs(out, exist_ok=True)
for f in fl:
    for me, op in (("a", "b"), ("b", "a")):
        if f[me] == "Alpha Rodeo" and f[me + "_id"] in ours and teams.get(f[op]) == f[op + "_id"]:
            href = f"/match/live/{f['a_id']}/{f['b_id']}"
            team = f[op]; tid = f[op + "_id"]
            fn = os.path.join(out, f"{tid}_vs_Alpha_Rodeo_{f[me+'_id']}.json")
            if os.path.exists(fn):
                continue
            try:
                d = scrape.parse_fight(scrape.get(href), href)
            except Exception as e:
                print("fail", href, e); continue
            d["entry_ids"] = {d["a"]: f["a_id"], d["b"]: f["b_id"]}
            d["when"] = f["when"]
            json.dump(d, open(fn, "w"), indent=1, ensure_ascii=False)
            print("saved", fn, d["a"], d["score_a"], d["b"], d["score_b"])
