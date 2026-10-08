"""Write a standalone bot file from cal_core.py + params."""
import re

CORE = open(__file__.replace("build.py", "cal_core.py")).read()


def body(params):
    src = CORE.split('"""', 2)[2]          # drop the module docstring
    src = src.replace("class Core:", "class Bot:")
    # inject params: replace defaults inside P = dict(...)
    start = src.index("    P = dict(")
    end = src.index("    )\n", start) + 6
    block = src[start:end]
    lines = block.splitlines()
    out = [lines[0]]
    for ln in lines[1:-1]:
        m = re.match(r"(\s+)(\w+)=(.*?),(\s+#.*)?$", ln)
        if m and m.group(2) in params:
            v = params[m.group(2)]
            out.append(f"{m.group(1)}{m.group(2)}={v!r},{m.group(4) or ''}")
        else:
            out.append(ln)
    out.append(lines[-1])
    return src[:start] + "\n".join(out) + "\n" + src[end:]


def write(path, name, params, doc="calibration candidate"):
    head = f"# Team Name: Zoo - {name}\n# Members: Organisers\n# Mentor: None\n\n"
    with open(path, "w") as f:
        f.write(head + '"""\n' + doc.strip() + '\n"""\n' + body(params))
