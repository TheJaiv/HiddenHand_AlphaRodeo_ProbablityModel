import re, ast
def oldparams(path):
    src = open(path).read()
    s = src.index("    P = dict(")
    e = src.index("    )\n", s)
    out = {}
    for ln in src[s:e].splitlines()[1:]:
        m = re.match(r"\s+(\w+)=(.*?),(\s+#.*)?$", ln)
        if m:
            out[m.group(1)] = ast.literal_eval(m.group(2))
    return out
