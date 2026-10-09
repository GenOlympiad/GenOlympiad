# shared code: code_8adf97c46851

import re
def _text(ans):
    if isinstance(ans, dict):
        a = ans.get("answers") or [None]
        return a[0]
    return ans
def count_and_duplicates(ans, n_expected):
    """Count the two-digit numbers read and check that all expected numbers are distinct."""
    txt = _text(ans)
    if txt is None:
        return {"n": 0, "n_distinct": 0, "count_ok": 0.0, "all_unique": 0.0, "unreadable": 1.0}
    toks = re.findall(r"\b\d{2}\b", str(txt))
    if not toks:
        return {"n": 0, "n_distinct": 0, "count_ok": 0.0, "all_unique": 0.0, "unreadable": 1.0}
    n = len(toks)
    n_distinct = len(set(toks))
    all_unique = 1.0 if (n == int(n_expected) and n_distinct == int(n_expected)) else 0.0
    dups = sorted(set(x for x in toks if toks.count(x) > 1))
    return {"n": n, "n_distinct": n_distinct, "dups": dups, "unreadable": 0.0,
            "count_ok": 1.0 if n == int(n_expected) else 0.0, "all_unique": all_unique}

# end of code_8adf97c46851
