# code: all_luhn_valid_code

import re
from collections import Counter


def _text(ans):
    if isinstance(ans, dict):
        a = ans.get("answers") or [None]
        return a[0]
    return ans


def _pass(ans):
    txt = _text(ans)
    out = {}
    if txt is None:
        return out
    for line in str(txt).splitlines():
        m = re.match(r"^\s*(?:row\s*)?(\d{1,3})\s*[:.)-]\s*(.+)$", line.strip(), re.I)
        if not m:
            continue
        d = re.sub(r"\D", "", m.group(2))
        if len(d) == 16:
            out[int(m.group(1))] = d
    return out


def luhn_valid(digs):
    s = 0
    for i, dgt in enumerate(reversed(digs)):
        pos = i + 1
        if pos % 2 == 0:
            v = dgt * 2
            if v > 9:
                v -= 9
            s += v
        else:
            s += dgt
    return s % 10 == 0


def all_luhn_valid(a1, a2, a3, n_expected):
    """Merge the transcriptions row by row and check every number passes the Luhn check."""
    passes = [p for p in (_pass(a1), _pass(a2), _pass(a3)) if p]
    if not passes:
        return {"n": 0, "n_valid": 0, "all_ok": 0.0, "unreadable": 1.0,
                "why": "no transcription came back"}
    keys = set()
    for p in passes:
        keys |= set(p.keys())
    merged, disputed = {}, []
    for k in sorted(keys):
        vals = [p[k] for p in passes if k in p]
        c = Counter(vals).most_common(1)[0]
        if len(vals) >= 2 and c[1] < 2:
            disputed.append(k)
            continue
        merged[k] = c[0]
    if disputed:
        return {"n": len(merged), "n_valid": 0, "all_ok": 0.0, "unreadable": 1.0,
                "disputed_rows": disputed, "why": "the passes disagree on a row's digits"}
    if len(merged) != int(n_expected):
        return {"n": len(merged), "n_valid": 0, "all_ok": 0.0, "unreadable": 1.0,
                "why": "the register did not transcribe in full"}
    bad = [k for k, s in merged.items() if not luhn_valid([int(c) for c in s])]
    n_valid = len(merged) - len(bad)
    return {"n": len(merged), "n_valid": n_valid, "bad_rows": sorted(bad),
            "all_ok": 1.0 if not bad else 0.0, "unreadable": 0.0}

# end of all_luhn_valid_code

# code: luhn_row_check_code
def luhn_row_check(gd):
    """Whether the sixteen-digit number passes the Luhn check, or is malformed."""
    import re
    digits = re.sub(r'\D', '', str(gd))
    if len(digits) != 16:
        return 'malformed'
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return 'valid' if total % 10 == 0 else 'invalid'

# end of luhn_row_check_code
