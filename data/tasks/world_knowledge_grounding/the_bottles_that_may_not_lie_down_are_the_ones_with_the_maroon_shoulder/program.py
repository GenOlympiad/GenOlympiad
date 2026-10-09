# shared code: map_code

import re

def normalise(s):
    return " ".join(str(s or "").lower().replace("-", " ").replace("*", "").replace("_", " ").split())

def _wb(tok, hay, start=0):
    m = re.compile(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(normalise(tok))).search(hay, start)
    return m.start() if m else -1

def match_answer_state(ans, table):
    """Map the answer to the one table state whose key phrase it contains, else refuse."""
    a = normalise(ans)
    if not a:
        return {"state": None, "refused": True}
    matches = [s for s, keys in table.items() if any(normalise(k) in a for k in keys)]
    if len(matches) == 1:
        return {"state": matches[0], "refused": False}
    return {"state": None, "refused": True}

_NUMWORD = {"zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,
            "nine":9,"ten":10,"eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,
            "sixteen":16}
_NW = (r"(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen"
       r"|fourteen|fifteen|sixteen)")
_NUM = r"(?:\d{1,3}|" + _NW + r")"

_UNIT = (r"(?:mm|cm|km|nm|um|micron|microns|millimet(?:re|er)s?|centimet(?:re|er)s?|"
         r"met(?:re|er)s?|kilomet(?:re|er)s?|inch|inches|ft|feet|foot|yard|yards|mile|miles|"
         r"kg|kgs|gram|grams|mg|lb|lbs|oz|ton|tons|tonne|tonnes|"
         r"ml|litre|litres|liter|liters|gallon|gallons|"
         r"sec|secs|second|seconds|min|mins|minute|minutes|hour|hours|hr|hrs|day|days|"
         r"deg|degree|degrees|percent|psi|bar|kpa|mpa|kn|newton|newtons|"
         r"volt|volts|amp|amps|watt|watts|kw|hz|rpm|px|pixel|pixels|pt|"
         r"mph|kph|am|pm|celsius|fahrenheit)")

_MARK = (r"(?:therefore|thus|hence|in\s+total|in\s+all|all\s+in\s+all|in\s+summary|in\s+conclusion|"
         r"overall|altogether|to\s+summari[sz]e|so|that\s+makes|that\s+gives|which\s+makes|"
         r"which\s+gives|counting\s+these|the\s+answer\s+is|final\s+answer|"
         r"(?:i|we)\s+(?:have|count|counted|make\s+it)|in\s+short)")
_MARK_CLAUSE = r"(?:^|[.:;]\s+|,\s+|\*\s+)" + _MARK + r"\b[^.;:]{0,160}"

_SLOTS_STRONG = [
    r"\\boxed\s*\{\s*(\d{1,3})\s*\}",
    r"(?:final\s+answer|the\s+answer|the\s+count|the\s+number|the\s+total|the\s+tally)"
    r"\s*(?:is|are|:|=)\s*\$?\s*(%s)\b" % _NUM,
    r"\bthere\s+(?:are|is|were|was)\s+(?:only\s+|just\s+|exactly\s+|about\s+|a\s+total\s+of\s+|"
    r"in\s+total\s+)?(%s)\b" % _NUM,
    r"(?:a\s+)?total\s+of\s+(%s)\b" % _NUM,
    r"\b(%s)\s+in\s+total\b" % _NUM,
    r"\bin\s+total\s*,?\s*(?:there\s+(?:are|is)\s+)?(%s)\b" % _NUM,
    r"\baltogether\s*,?\s*(%s)\b" % _NUM,
    r"\b(%s)\s+altogether\b" % _NUM,
    r"\b(?:count|number|total|tally)\s*(?:is|:|=)\s*(%s)\b" % _NUM,
    r"=\s*(%s)\s+[a-z]" % _NUM,
    r"\b(?:i|we)\s+(?:can\s+|could\s+|am\s+able\s+to\s+|are\s+able\s+to\s+)?(?:\w+ly\s+)?"
    r"(?:see|count|counted|find|found|identify|identified|make\s+out|have)"
    r"\s+(?:only\s+|just\s+|exactly\s+|a\s+total\s+of\s+)?(%s)\b" % _NUM,
]

_SLOTS_WEAK = [
    r"\b(?:all|only|just|exactly|both)?\s*(%s)\s+of\s+(?:the|these|those|them|which|it)\b" % _NUM,
    r"\b(?:all|both)\s+(%s)\s+[a-z]" % _NUM,
    r"\b(%s)\s+(?:separate|distinct|individual)\b" % _NUM,
    r"\b(%s)\s+(?:are|is)\s+(?:visible|present|shown|standing|open|in\s+view|fitted|hung|left|there)\b" % _NUM,
    r"^\s*(%s)\s*[.!]?\s*$" % _NUM,
    r"\bis\s+(%s)\s*[.!]?\s*$" % _NUM,
    r"\b(?:reach|reaches|reached|pass|passes|passed|extend|extends|extended|cross|crosses|"
    r"crossed|clear|clears|cleared|cover|covers|covered|go|goes|went)\s+"
    r"(?:past|beyond|over|up\s+to)\s+(%s)\b" % _NUM,
]

_SLOT_NEAR_MARK = r"\b(%s)\b" % _NUM

_SLOT_TAIL_NP = r"\b(%s)\s+(?:[a-z]+\s+){0,3}[a-z]+s\b" % _NUM

_ZERO_SLOTS = [
    r"there\s+(?:are|is|were|was)\s+(?:now\s+|currently\s+|absolutely\s+)?(?:no|none|not\s+any|zero)\b",
    r"there\s+(?:aren'?t|isn'?t|are\s+not|is\s+not|were\s+not|weren'?t)\s+any\b",
    r"\bthere\s+(?:are|is)\s+none\b",
    r"\bnone\s+of\s+(?:the|these|those|them|which|it)\b",
    r"\bnone\s+(?:are|is|were|was|have|has|appear|appears|seem|seems)\b",
    r"\bnone\s+at\s+all\b",
    r"^\s*none\b",
    r"\bnot\s+a\s+single\b",
    r"\bneither\s+of\b",
    r"\b(?:i|we)\s+(?:can|could)\s+see\s+no\b",
    r"\b(?:i|we)\s+(?:cannot|can\s*not|do\s+not|don'?t|did\s+not|didn'?t)\s+see\s+any\b",
    r"\bthe\s+answer\s+(?:is|:)\s*(?:none|zero)\b",
    r"\bzero\b",
    r"\bno\s+[a-z][a-z ]{0,44}?\s+(?:are|is)\s+"
    r"(?:visible|present|shown|standing|open|fitted|hung|used|left|crossed|twisted|chocked|rolled)\b",
]


def _paren_spans(a):
    spans, stack = [], []
    for i, ch in enumerate(a):
        if ch == "(":
            stack.append(i)
        elif ch == ")" and stack:
            spans.append((stack.pop(), i))
    return spans


def _in_spans(spans, pos):
    return any(s <= pos <= e for s, e in spans)


def _sentences(a):
    out, start = [], 0
    for m in re.finditer(r"(?<!\d)[.!?;]\s+", a):
        out.append((start, m.start()))
        start = m.end()
    out.append((start, len(a)))
    return [(s, e) for s, e in out if e > s]


def _mark_spans(a):
    return [(m.start(), m.end()) for m in re.finditer(_MARK_CLAUSE, a)]


def _is_enumerated(a):
    n = len(re.findall(r"(?:^|[.:;]\s+)\d{1,2}\s*[.)]\s+[a-z*]", a))
    n += len(re.findall(r"(?:^|\s)\*\s+\*?\*?[a-z]", a))
    return n >= 2


def _conclusion_spans(a):
    ss = _sentences(a)
    sp = list(_mark_spans(a))
    if ss:
        sp.append(ss[0])
        if not _is_enumerated(a):
            sp.append(ss[-1])
    return sp


def _val(tok):
    tok = tok.strip()
    return _NUMWORD[tok] if tok in _NUMWORD else int(tok)


def count_of(ans):
    """Pull the final stated count out of a free-text answer, or refuse if none is found."""
    a = normalise(ans)
    if not a:
        return {"state": None, "refused": True}
    parens = _paren_spans(a)

    def _ok(a_, p, end):
        if _in_spans(parens, p):
            return False
        if re.match(r"\s*" + _UNIT + r"(?![a-z])", a_[end:end + 24]):
            return False
        if re.match(r"\.\d", a_[end:end + 2]):
            return False
        if p >= 1 and re.search(r"\d\.$", a_[max(0, p - 2):p]):
            return False
        if re.match(r"\s*[.)]\s+[a-z*]", a_[end:end + 4]) and (
                p == 0 or re.search(r"(?:^|[.:;*]\s+)$", a_[max(0, p - 3):p])):
            return False
        if re.search(r"\bnot\s+(?:a\s+)?(?:single\s+)?$", a_[max(0, p - 18):p]):
            return False
        return True

    def _scan(pats, hay_spans=None):
        best = None
        for pat in pats:
            for m in re.finditer(pat, a):
                p, end = m.start(1), m.end(1)
                if hay_spans is not None and not _in_spans(hay_spans, p):
                    continue
                if not _ok(a, p, end):
                    continue
                if best is None or p >= best[0]:
                    best = (p, _val(m.group(1)))
        return best

    marks = _mark_spans(a)
    cands = []

    if marks:
        got = _scan(_SLOTS_STRONG + _SLOTS_WEAK, marks)
        if got is None:
            for s, e in marks:
                for m in re.finditer(_SLOT_NEAR_MARK, a[s:e]):
                    p, end = s + m.start(1), s + m.end(1)
                    if _ok(a, p, end):
                        got = (p, _val(m.group(1))) if (got is None or p > got[0]) else got
                        break
        if got is not None:
            cands.append(got)

    got = _scan(_SLOTS_STRONG)
    if got is not None:
        cands.append(got)
    if cands:
        return {"state": max(cands, key=lambda x: x[0])[1], "refused": False}

    got = _scan(_SLOTS_WEAK)
    if got is not None:
        return {"state": got[1], "refused": False}


    concl = _conclusion_spans(a)
    for pat in _ZERO_SLOTS:
        for m in re.finditer(pat, a):
            if _in_spans(concl, m.start()) and not _in_spans(parens, m.start()):
                return {"state": 0, "refused": False, "zero_read": m.group(0).strip()}

    return {"state": None, "refused": True}

def bucket_of(ans, cap):
    c = count_of(ans)
    if c["refused"] or c["state"] is None:
        return {"state": None, "refused": True}
    n = int(c["state"])
    return {"state": ("%d_or_more" % cap if n >= cap else str(n)), "refused": False, "n": n}

def seq_colours(ans, vocab):
    a = normalise(ans)
    if not a:
        return {"state": None, "refused": True}
    hits = []
    for m in re.finditer(r"(?<![a-z])(%s)(?![a-z])" % "|".join(sorted(vocab, key=len, reverse=True)), a):
        w = m.group(1)
        if not hits or hits[-1] != w:
            hits.append(w)
    if not hits:
        return {"state": None, "refused": True}
    return {"state": ",".join(hits), "refused": False, "seq": hits}

def eq_int(ans, want):
    c = count_of(ans)
    if c["refused"] or c["state"] is None:
        return {"state": None, "refused": True}
    return {"state": str(int(c["state"])), "refused": False}

TAB_part1 = {"capped": ["a screwed on cap over each valve", "screwed on cap", "cap over each valve", "caps over the valves", "a cap over the valve", "valve caps", "protective cap", "each valve has a cap", "cap screwed on", "all four are capped", "caps covering the valves", "white caps", "a black cap", "black caps", "cap covering the valve"], "bare": ["bare valves", "nothing over them", "uncovered valves", "exposed valves", "the valves are bare", "open valves with no cap", "valves left bare", "naked valves"], "mixed": ["some capped and some bare", "some with caps and some without", "some have caps and some do not", "two capped and two bare", "not all the same at the valve end"], "unseen": ["the valve ends are not visible", "valve ends are not visible", "valve ends cannot be seen", "valve ends are hidden", "valve ends are out of shot"], "no_valve": ["no valves at all", "no valves anywhere", "none of them has a valve", "plain domed tops with no fitting"]}
ASET_part1 = ["a screwed on cap over each valve", "the valves are bare, nothing over them", "some capped and some bare", "the valve ends are not visible", "none of them has a valve, plain domed tops with no fitting"]

# end of map_code
