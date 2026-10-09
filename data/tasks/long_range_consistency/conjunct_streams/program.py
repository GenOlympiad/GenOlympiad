# code: helpers
from genolympiad.task_helpers import join_box_reads
# end of helpers

# shared code: code_ecf10481b3c0

import re


def _tok(a):
    return re.sub(r"[^a-z0-9]", "", str(a).lower())


_LEAD = re.compile(r"^(?:panel|slot|row|bay|peg|photo|picture|number|no)*\d{0,2}$")


def _one(a, k):
    if a is None:
        return 0.0
    if isinstance(a, (list, tuple)):
        a = a[0] if a else None
    s, t = _tok(a), _tok(k)
    if not t:
        return 0.0
    if s == t:
        return 1.0
    if s.endswith(t) and _LEAD.match(s[:len(s) - len(t)]):
        return 1.0
    return 0.0


def _slots(got, want):
    if isinstance(got, dict) or not isinstance(got, (list, tuple)) or len(got) < len(want):
        return None
    return [_one(got[i], w) for i, w in enumerate(want)]


def verdict(gots, wants):
    slots = []
    for g, w in zip(gots, wants):
        if not w:
            continue
        s = _slots(g, w)
        if s is None:
            return {"law": 0.0, "share": 0.0, "unreadable": True, "bad": None}
        slots += s
    if not slots:
        return {"law": 0.0, "share": 0.0, "unreadable": True, "bad": None}
    ok = sum(slots)
    return {"law": 1.0 if ok == len(slots) else 0.0,
            "share": round(ok / float(len(slots)), 4), "unreadable": False,
            "bad": [i for i, v in enumerate(slots) if v == 0.0]}

# end of code_ecf10481b3c0

# code: verdict_law_code
import re
def _one(a, k):
    if a is None: return 0.0
    s = re.sub(r"[^a-z0-9]", "", str((a[0] if a else None) if isinstance(a, (list, tuple)) else a).lower()); t = re.sub(r"[^a-z0-9]", "", str(k).lower())
    return 0.0 if not t else (1.0 if (s == t or (s.endswith(t) and re.match(r"^(?:panel|slot|row|bay|peg|photo|picture|number|no)*\d{0,2}$", s[:len(s) - len(t)]))) else 0.0)
def score_slot_matches(reads, expected):
    """Whether every read slot matches its expected word, with the share that match."""
    slots = []
    for g, w in zip(reads, expected):
        if w and (isinstance(g, dict) or not isinstance(g, (list, tuple)) or len(g) < len(w)): return {'law': 0.0, 'share': 0.0, 'unreadable': True, 'refused': True, 'bad': None}
        slots += [_one(g[i], x) for i, x in enumerate(w)] if w else []
    if not slots: return {'law': 0.0, 'share': 0.0, 'unreadable': True, 'refused': True, 'bad': None}
    return {'law': 1.0 if sum(slots) == len(slots) else 0.0, 'share': round(sum(slots) / float(len(slots)), 4), 'unreadable': False, 'bad': [i for i, v in enumerate(slots) if v == 0.0]}

# end of verdict_law_code

# code: verdict_share_code
import re
def _one(a, k):
    if a is None: return 0.0
    s = re.sub(r"[^a-z0-9]", "", str((a[0] if a else None) if isinstance(a, (list, tuple)) else a).lower()); t = re.sub(r"[^a-z0-9]", "", str(k).lower())
    return 0.0 if not t else (1.0 if (s == t or (s.endswith(t) and re.match(r"^(?:panel|slot|row|bay|peg|photo|picture|number|no)*\d{0,2}$", s[:len(s) - len(t)]))) else 0.0)
def score_slot_matches(reads, expected):
    """Whether every read slot matches its expected word, with the share that match."""
    slots = []
    for g, w in zip(reads, expected):
        if w and (isinstance(g, dict) or not isinstance(g, (list, tuple)) or len(g) < len(w)): return {'law': 0.0, 'share': 0.0, 'unreadable': True, 'refused': True, 'bad': None}
        slots += [_one(g[i], x) for i, x in enumerate(w)] if w else []
    if not slots: return {'law': 0.0, 'share': 0.0, 'unreadable': True, 'refused': True, 'bad': None}
    return {'law': 1.0 if sum(slots) == len(slots) else 0.0, 'share': round(sum(slots) / float(len(slots)), 4), 'unreadable': False, 'bad': [i for i, v in enumerate(slots) if v == 0.0]}

# end of verdict_share_code

# code: cov_code

import re, difflib


def _c(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def line_coverage(text, lines):
    """Share of expected lines found in the read text, allowing near matches."""
    s = _c(text)
    lines = list(lines or [])
    if not lines:
        return 0.0
    found = 0
    for line in lines:
        t = _c(line)
        if not t:
            found += 1
            continue
        if t in s:
            found += 1
            continue
        best, n = 0.0, len(t)
        step = max(1, n // 8)
        for i in range(0, max(1, len(s) - n + 1), step):
            best = max(best, difflib.SequenceMatcher(a=t, b=s[i:i + n + 3]).ratio())
        found += 1 if best >= 0.82 else 0
    return round(found / float(len(lines)), 4)

# end of cov_code
