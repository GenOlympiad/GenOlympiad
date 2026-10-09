# code: helpers
from genolympiad.task_helpers import to_float
# end of helpers

# shared code: code_34bd7882bda1

import re


def _sp_clean(s):
    return re.sub(r"[^a-z]", "", str(s).lower())


def _sp_rows(vseq, n_lines):
    if not isinstance(vseq, (list, tuple)):
        return None
    got = {}
    for s in vseq:
        if isinstance(s, (list, tuple)):
            s = " ".join(str(x) for x in s)
        m = re.match(r"^\s*[\(\[]?\s*(\d{1,2})\s*[:.\)\]]\s*(.*)$", str(s).strip())
        if not m:
            continue
        k = int(m.group(1))
        if 1 <= k <= int(n_lines) and k not in got:
            got[k] = _sp_clean(m.group(2))
    if any((i not in got) or (not got[i]) for i in range(1, int(n_lines) + 1)):
        return None
    return [got[i] for i in range(1, int(n_lines) + 1)]


def _sp_out(n_bad, n_units, unreadable=False, note=""):
    if unreadable:
        return {"unreadable": 1.0, "ok": 0.0, "frac": 0.0, "bad": -1.0, "n": 0.0, "note": note}
    n_units = max(1, int(n_units))
    n_bad = max(0, int(n_bad))
    return {"unreadable": 0.0, "ok": (1.0 if n_bad == 0 else 0.0),
            "frac": max(0.0, (n_units - n_bad) / float(n_units)),
            "bad": float(n_bad), "n": float(n_units), "note": note}


def score_reversed_spelled(letter_reads, n_lines, sources):
    """Count rows whose letter-by-letter reading differs from the reversed source word."""
    got = _sp_rows(letter_reads, n_lines)
    if got is None:
        return _sp_out(0, 0, unreadable=True,
                       note="the letter read did not return all %d rows" % int(n_lines))
    bad = 0
    for i, g in enumerate(got):
        want = _sp_clean(sources[i])[::-1]
        if g != want:
            bad += 1
    return _sp_out(bad, int(n_lines), note="rows=%d" % int(n_lines))


def unit_rows(vseq, n_lines, sources):
    got = _sp_rows(vseq, n_lines)
    if got is None:
        return []
    out = []
    for i, g in enumerate(got):
        want = _sp_clean(sources[i])[::-1]
        out.append({"n": i + 1, "ok": (g == want),
                    "label": "printed '%s' / wanted '%s'" % (g, want)})
    return out

# end of code_34bd7882bda1

# shared code: code_a94ff78ee612

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

def score_reversed_words(rows, n_lines, sources):
    """Count lines whose last word is not the source word reversed, allowing one slip."""
    body = _body(rows, n_lines)
    if body["lines"] is None:
        return _out(0, 0, unreadable=True, note="entries not recovered")
    bad = 0
    for i, ln in enumerate(body["lines"]):
        words = _words([ln])
        want = str(sources[i]).lower()[::-1]
        got = words[-1] if words else ""
        if not _ed1(got, want):
            bad += 1
    return _out(bad + body["extra"], n_lines, note="n=%d" % n_lines)


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


def _spelled_pass(v):
    if not isinstance(v, (list, tuple)):
        return None
    rows = []
    for s in v:
        if isinstance(s, (list, tuple)):
            s = " ".join(str(x) for x in s)
        m = re.match(r"^\s*[\(\[]?\s*(\d{1,2})\s*[:.\)\]]\s*(.*)$", str(s).strip())
        if not m:
            continue
        parts = [re.sub(r"[^A-Za-z]", "", p) for p in re.split(_SEP, m.group(2).strip())]
        parts = [p for p in parts if p]
        if not parts:
            continue
        if all(len(p) == 1 for p in parts):
            head, letters = "", "".join(parts)
        else:
            head, letters = parts[0], "".join(parts[1:])
        if not letters:
            continue
        toks = [{"text": m.group(1) + "."}]
        if head:
            toks.append({"text": head})
        toks.append({"text": letters})
        rows.append(toks)
    return rows or None


def _passes_sp(v, *ts):
    sp = _spelled_pass(v)
    return ([sp] if sp else []) + _passes(*ts)

# end of code_a94ff78ee612
