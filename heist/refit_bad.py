"""heist/refit_bad.py - refit every team whose imitation is not calibrated (data/calib.json)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_field   # noqa: E402

cal = json.load(open(os.path.join(HERE, "data", "calib.json")))
bad = [t for t, rows in cal.items() if not all(abs(r["local"] - r["live"]) <= 1.5 for r in rows)]
sys.argv = ["build_field.py", "--iters", sys.argv[1] if len(sys.argv) > 1 else "2500", "--teams"] + bad
build_field.main()
