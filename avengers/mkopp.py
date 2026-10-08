"""avengers/mkopp.py - write avengers/opp/opp_<team>.py from opp_core + refit params (data/refits.json)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = open(os.path.join(HERE, "..", "heist", "opp_core.py")).read()
REFITS = json.load(open(os.path.join(HERE, "data", "refits.json")))

# hand fixes informed by the answer analysis (ansfit.py) and heist's calib experience
FIXES = {
    # round-1 answers: Cyberpsycho never takes in round 1
    "Cyberpsycho": {"R1L": 0},
    # Godtier also never takes in round 1
    "Godtier": {"R1L": 0},
    # Imposters: TH=7 (fit) but take exactly 1 lot in round 1; keep R1L=1
}

HEADER = """# Team Name: Field model - {team}
# Members: none (local imitation, never uploaded)
# Mentor: none
\"\"\"opp_{slug}.py - avengers imitation of live team {team} #{entry}, fitted to public replays
(avengers/refit.py, seed 2): quote err {qerr}, respond miss {rmiss}, move miss {mmiss}.
Same opp_core as heist/opp_core.py; see it for parameter meanings.\"\"\"

"""


def slug(t):
    return t.lower().replace(" ", "_").replace("-", "_")


def main():
    for team, d in REFITS.items():
        if d["plays"] == 0:
            continue
        P = dict(d["P"])
        P.update(FIXES.get(team, {}))
        # use the same DEFAULT dict as opp_core so params stay meaningful
        out = CORE.rstrip() + "\n\n\nBot = make_bot(" + json.dumps(P) + ")\n"
        # opp_core ends with `return Bot`; we append the instantiation after it
        fn = os.path.join(HERE, "opp", f"opp_{slug(team)}.py")
        head = HEADER.format(team=team, slug=slug(team), entry=d["entry"], qerr=d["loss"],
                             rmiss=d["loss"], mmiss=d["loss"])
        # simpler: reuse the fit line below
        head = (f"# Team Name: Field model - {team}\n"
                f"# Members: none (local imitation, never uploaded)\n"
                f"# Mentor: none\n"
                f"\"\"\"opp_{slug(team)}.py - avengers imitation of live team {team} #{d['entry']}, "
                f"fitted to public replays (avengers/refit.py seed 2), loss {d['loss']:.3f}.\n"
                f"Same opp_core as heist/opp_core.py; see it for parameter meanings.\"\"\"\n\n")
        open(fn, "w").write(head + out)
        print("wrote", fn)


if __name__ == "__main__":
    main()
