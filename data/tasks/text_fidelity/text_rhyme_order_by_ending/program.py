# code: helpers
from genolympiad.task_helpers import to_float
# end of helpers

# shared code: code_5c5d84c7387a

import re

_SEP = r"[\s=→»|]+"


def _junk_row(joined):
    toks = [t for t in re.split(_SEP, str(joined).strip()) if t]
    if not toks:
        return True
    letters = sum(len(re.sub(r"[^A-Za-z]", "", t)) for t in toks)
    long_toks = sum(1 for t in toks if len(re.sub(r"[^A-Za-z]", "", t)) >= 3)
    return letters < 6 or long_toks == 0


def _read_quality(words):
    if not words:
        return (-1.0, 0)
    longish = sum(1 for w in words if len(re.sub(r"[^A-Za-z]", "", str(w))) >= 3)
    return (round(longish / float(len(words)), 2), len(words))


def _rowsets(reads):
    if reads is None:
        return []
    if isinstance(reads, (str, dict)):
        reads = [reads]
    out = []
    for r in reads:
        if isinstance(r, dict):
            a = r.get("answers") or []
            t = a[0] if a else None
        else:
            t = r
        if t:
            out.append(str(t))
    return out


def _lines_of(txt):
    return [ln.strip() for ln in str(txt).replace("\r", "\n").split("\n") if ln.strip()]


_MARKER = re.compile(r"^[\(\[]?\s*([0-9lLIO]{1,2})\s*(?:[.)\]:>\-。．、,·|]\s*|\s+)(.*)$")


def _parse_pass(txt, n_lines):
    got, extra, cur = {}, 0, None
    for joined in _lines_of(txt):
        m = _MARKER.match(joined)
        if m:
            num = m.group(1).translate(str.maketrans({"l": "1", "L": "1", "I": "1", "O": "0"}))
            if num.isdigit():
                k = int(num)
                words = [w for w in re.split(_SEP, m.group(2).strip()) if w]
                if 1 <= k <= n_lines and k not in got:
                    got[k] = words
                    cur = k
                else:
                    extra += 1
                    cur = None
                continue
        if cur is not None and not _junk_row(joined):
            got[cur].extend(w for w in re.split(_SEP, joined) if w)
    return got, extra


def _body(reads, n_lines):
    got, extra = {}, 0
    for txt in _rowsets(reads):
        g, e = _parse_pass(txt, n_lines)
        extra = max(extra, e)
        for k, v in g.items():
            if k not in got or _read_quality(v) > _read_quality(got[k]):
                got[k] = v
    if len(got) != n_lines or any(not got[k] for k in got):
        return {"lines": None, "extra": extra}
    return {"lines": [got[k] for k in range(1, n_lines + 1)], "extra": extra}




def _clean(w):
    return re.sub(r"[^a-z]", "", str(w).lower())


def _words(lines):
    out = []
    for ln in lines:
        for w in ln:
            c = _clean(w)
            if c:
                out.append(c)
    return out


def _too_short(ln, min_words):
    letters = sum(len(_clean(w)) for w in ln)
    return len(ln) < int(min_words) and letters < int(int(min_words) * 3.4)


def _out(n_bad, n_units, unreadable=False, note=""):
    if unreadable:
        return {"unreadable": 1.0, "ok": 0.0, "frac": 0.0, "bad": -1.0, "n": 0.0, "note": note}
    n_units = max(1, int(n_units))
    return {"unreadable": 0.0, "ok": (1.0 if n_bad == 0 else 0.0),
            "frac": max(0.0, (n_units - n_bad) / float(n_units)),
            "bad": float(n_bad), "n": float(n_units), "note": note}


def _is_caps(w):
    letters = re.sub(r"[^A-Za-z]", "", str(w))
    if len(letters) < 3:
        return False
    ups = sum(1 for ch in letters if ch.isupper())
    return ups >= 2 and (ups / float(len(letters))) >= 0.5


def _ed1(a, b):
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(1 for x, y in zip(a, b) if x != y) <= 1
    if la > lb:
        a, b, la, lb = b, a, lb, la
    for i in range(lb):
        if a == b[:i] + b[i + 1:]:
            return True
    return False

def score_rhyme_order(reads, n_lines, expected):
    """Count lines whose first word differs from the expected word in rhyme order."""
    body = _body(reads, n_lines)
    if body["lines"] is None:
        return _out(0, 0, unreadable=True, note="entries not recovered")
    bad = 0
    for i, ln in enumerate(body["lines"]):
        words = _words([ln])
        got = words[0] if words else ""
        if got != str(expected[i]).lower():
            bad += 1
    return _out(bad + body["extra"], n_lines, note="n=%d" % n_lines)

# end of code_5c5d84c7387a
