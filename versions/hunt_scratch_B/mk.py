"""mk.py - make a variant: python mk.py BASE OUT "idea" 'old1' 'new1' ['old2' 'new2' ...]
Each old string must occur exactly once in BASE (asserted). Header line 4 rewritten."""
import sys
from pathlib import Path
base, out, idea, *subs = sys.argv[1:]
src = Path(base).read_text()
lines = src.split("\n")
assert lines[3].startswith("# Version:")
lines[3] = f"# Version: {Path(out).stem}, parent {base}, idea: {idea}"
src = "\n".join(lines)
for o, n in zip(subs[::2], subs[1::2]):
    c = src.count(o)
    assert c == 1, (o, c)
    src = src.replace(o, n)
Path(out).write_text(src)
print("wrote", out)
