# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_e201c5da4161
import re
def first_answer(node):
    if isinstance(node, dict):
        a = node.get('answers') or [None]
        return a[0]
    return node
def bits(node):
    ans = first_answer(node)
    if ans is None:
        return None
    s = str(ans)
    best = ''
    for m in re.finditer(r'[01](?:[\s,]*[01])*', s):
        if len(re.findall(r'[01]', m.group(0))) > len(re.findall(r'[01]', best)):
            best = m.group(0)
    got = re.findall(r'[01]', best)
    return got or None
def row_exact(node, target_row):
    """1 if the binary digits read for a row equal the reference row exactly, else 0."""
    got = bits(node)
    if not got:
        return 0.0
    tgt = [str(x).strip() for x in target_row]
    return 1.0 if got == tgt else 0.0
def row_frac(node, target_row):
    """The share of reference row digits matched position by position in the read row."""
    got = bits(node)
    if not got:
        return 0.0
    tgt = [str(x).strip() for x in target_row]
    ok = sum(1 for i in range(len(tgt)) if i < len(got) and got[i] == tgt[i])
    return round(ok / len(tgt), 4) if tgt else 0.0

# end of code_e201c5da4161

# code: row_frac_code
def row_frac(row, target_row):
    """The share of reference row digits matched position by position in the read row."""
    if not row or not isinstance(row, (list, tuple)):
        return 0.0
    got = [str(x).strip() for x in row]
    tgt = [str(x).strip() for x in target_row]
    ok = sum(1 for i in range(len(tgt)) if i < len(got) and got[i] == tgt[i])
    return round(ok / len(tgt), 4) if tgt else 0.0

# end of row_frac_code
