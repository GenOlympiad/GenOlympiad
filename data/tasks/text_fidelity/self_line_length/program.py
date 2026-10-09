# code: helpers
from genolympiad.task_helpers import to_float
# end of helpers

# shared code: code_1bd3b78ab971

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
    t = str(txt).replace("\r", "\n").replace("|", "\n")
    return [ln.strip() for ln in t.split("\n") if ln.strip()]


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


_NUMBER_HEAD = re.compile(r"^\s*[\(\[]?\s*\d{1,2}\s*[.)\]:>\-]?\s*")


def _vlm_lines(vseq, n_lines):
    if not isinstance(vseq, (list, tuple)) or len(vseq) < int(n_lines):
        return None
    out = []
    for s in list(vseq)[:int(n_lines)]:
        if isinstance(s, (list, tuple)):
            s = " ".join(str(x) for x in s)
        t = _NUMBER_HEAD.sub("", str(s).strip())
        toks = [w for w in re.split(r"\s+", t) if w]
        if not toks:
            return None
        out.append(toks)
    return out


def _clean(w):
    return re.sub(r"[^a-z]", "", str(w).lower())


def _toks(ln):
    return [w for w in (_clean(x) for x in ln) if w]


def _words(lines):
    out = []
    for ln in lines:
        out.extend(_toks(ln))
    return out


def _too_short(ln, min_words):
    letters = sum(len(_clean(w)) for w in ln)
    return len(ln) < int(min_words) and letters < int(int(min_words) * 3.4)


def _out(n_bad, n_units, unreadable=False, note=""):
    if unreadable:
        return {"unreadable": 1.0, "ok": 0.0, "frac": 0.0, "bad": -1.0, "n": 0.0, "note": note}
    n_units = max(1, int(n_units))
    n_bad = max(0, int(n_bad))
    return {"unreadable": 0.0, "ok": (1.0 if n_bad == 0 else 0.0),
            "frac": max(0.0, (n_units - n_bad) / float(n_units)),
            "bad": float(n_bad), "n": float(n_units), "note": note}


def _run(vseq, reads, n_lines, check):
    n_lines = int(n_lines)
    lv = _vlm_lines(vseq, n_lines)
    if lv is None:
        return _out(0, 0, unreadable=True,
                    note="VLM transcription did not return %d body lines" % n_lines)
    cands = [lv]
    b = _body(reads, n_lines)
    if b["lines"] is not None and [len(_toks(x)) for x in b["lines"]] == [len(_toks(x)) for x in lv]:
        cands.append(b["lines"])
    best = None
    for lines in cands:
        n_bad, n_units, note = check(lines)
        r = _out(n_bad + b["extra"], n_units + (1 if b["extra"] else 0), note=note)
        if best is None or (r["ok"], r["frac"]) > (best["ok"], best["frac"]):
            best = r
    return best

def word_count_equals_first_word_length(vseq, reads, n_lines, min_words, cover):
    """Score lines whose word count equals the first word's length, counts all distinct."""
    def check(lines):
        bad, counts = 0, []
        for ln in lines:
            ws = _toks(ln)
            if not ws:
                bad += 1
                counts.append(0)
                continue
            counts.append(len(ws))
            if len(ws) != len(ws[0]) or len(ws) < int(min_words):
                bad += 1
        units = len(lines) + 1
        if len(set(counts)) != len(counts):
            bad += 1
        if cover:
            units += 1
            if sorted(counts) != sorted(int(x) for x in cover):
                bad += 1
        return bad, units, "counts=%s" % ",".join(str(c) for c in counts)
    return _run(vseq, reads, n_lines, check)


def distinct_line_counts(vseq, reads, n_lines):
    """1 if every line has a different number of words, else 0."""
    def check(lines):
        counts = [len(_toks(ln)) for ln in lines]
        return (0 if len(set(counts)) == len(counts) else 1), 1, \
               "counts=%s" % ",".join(str(c) for c in counts)
    return _run(vseq, reads, n_lines, check)

# end of code_1bd3b78ab971
