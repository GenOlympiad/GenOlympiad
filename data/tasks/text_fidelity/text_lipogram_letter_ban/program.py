# code: helpers
from genolympiad.task_helpers import to_float
# end of helpers

# shared code: code_db197f4ad80d

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


def _rowsets(rows):
    if not rows:
        return []
    first = rows[0]
    if first and isinstance(first[0], dict):
        return [rows]
    return [p for p in rows if p]


def _body(rows, n_lines):
    got, extra = {}, 0
    for rowset in _rowsets(rows):
        g, e = _parse_pass(rowset, n_lines)
        extra = max(extra, e)
        for k, v in g.items():
            if k not in got or _read_quality(v) > _read_quality(got[k]):
                got[k] = v
    if len(got) != n_lines or any(not got[k] for k in got):
        return {"lines": None, "extra": extra}
    return {"lines": [got[k] for k in range(1, n_lines + 1)], "extra": extra}


_MARKER = re.compile(r"^[\(\[]?\s*([0-9lLIO]{1,2})\s*(?:[.)\]:>\-。．、,·]\s*|\s+)(.*)$")


def _parse_pass(rows, n_lines):
    got, extra, cur = {}, 0, None
    for r in rows or []:
        toks = [str(t.get("text", "")).strip() for t in (r or [])]
        joined = " ".join(t for t in toks if t).strip()
        if not joined:
            continue
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

def score_lipogram(rows, n_lines, banned, min_words):
    """Count words containing the banned letter, plus lines that are too short."""
    body = _body(rows, n_lines)
    if body["lines"] is None:
        return _out(0, 0, unreadable=True, note="body lines not recovered")
    lines = body["lines"]
    words = _words(lines)
    bad = sum(1 for w in words if banned in w)
    short = sum(1 for ln in lines if _too_short(ln, min_words))
    return _out(bad + short + body["extra"], len(words) + n_lines, note="banned=%s" % banned)


_DOUBLE = re.compile(r"^\s*\d{1,2}\s*[.)]\s+(?=\d{1,2}\s*[.)]\s)")


def _strip_added_numbering(lines):
    dbl = sum(1 for ln in lines if _DOUBLE.match(ln))
    if dbl < 3 or dbl < 0.4 * max(1, len(lines)):
        return lines
    return [re.sub(r"^\s*\d{1,2}\s*[.)]\s+", "", ln, count=1) for ln in lines]


def _vlm_rows(t):
    if isinstance(t, dict):
        a = t.get("answers") or []
        s = a[0] if a else None
    else:
        s = t
    if not s:
        return []
    rows = []
    lines = [ln for ln in str(s).replace("\r", "\n").split("\n") if ln.strip()]
    for line in _strip_added_numbering(lines):
        toks = [w for w in re.split(_SEP, line.strip()) if w]
        if toks:
            rows.append([{"text": w} for w in toks])
    return rows


def _passes(*ts):
    return [r for r in (_vlm_rows(t) for t in ts) if r]

# end of code_db197f4ad80d
