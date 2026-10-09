# shared code: code_a23d871dc0aa

import re


def _norm(s):
    return " " + re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip() + " "


def _word(w):
    return re.sub(r"[^a-z0-9]+", "", str(w).lower())


def _state(slot, yes_word, no_word):
    s = _norm(slot)
    y, n = _word(yes_word), _word(no_word)
    hy = bool(y) and (" " + y + " ") in s
    hn = bool(n) and (" " + n + " ") in s
    if hy and not hn:
        return 1
    if hn and not hy:
        return 0
    return None


def _flat(blocks):
    out = []
    for b in blocks:
        if b is None or isinstance(b, dict) or isinstance(b, str) or not isinstance(b, (list, tuple)):
            return None
        out += list(b)
    return out


def _keytoks(s):
    return [t.lower() for t in re.findall(r"[A-Za-z0-9]+", str(s if s is not None else ""))]


def _bind(got, labels, n):
    keys = [_keytoks(l) for l in (labels or [])]
    if len(keys) != n or any(not k for k in keys) or len(set(tuple(k) for k in keys)) != n:
        return None
    slots = [None] * n
    taken = [False] * n
    for g in got:
        toks = _keytoks(g)
        for i, k in enumerate(keys):
            if taken[i]:
                continue
            if len(toks) >= len(k) and toks[:len(k)] == k:
                slots[i] = g
                taken[i] = True
                break
    if not any(taken):
        return None
    return slots
def verdict(blocks, want_idx, n_items, yes_word, no_word, labels=None):
    got = _flat(blocks)
    n = int(n_items)
    if got is None or len(got) < n:
        return {"member": 0.0, "card": 0.0, "share": 0.0, "n_marked": -1,
                "read": [] if got is None else [str(x) for x in got], "want": [],
                "unreadable": True}
    want = [1 if i in set(int(x) for x in want_idx) else 0 for i in range(n)]
    bound = _bind(got, labels, n)
    if bound is None:
        bound = list(got[:n])
        keyed = False
    else:
        keyed = True
    st = [_state(bound[i], yes_word, no_word) if bound[i] is not None else None
          for i in range(n)]
    if sum(1 for x in st if x is None) * 2 > n:
        return {"member": 0.0, "card": 0.0, "share": 0.0, "n_marked": -1,
                "read": [str(x) for x in got[:n]], "want": want, "keyed": keyed,
                "unreadable": True}
    ok = [1.0 if (a is not None and a == w) else 0.0 for a, w in zip(st, want)]
    nm = sum(1 for a in st if a == 1)
    return {"member": 1.0 if sum(ok) == n else 0.0,
            "card": 1.0 if nm == sum(want) else 0.0,
            "share": round(sum(ok) / float(n), 4),
            "n_marked": nm, "read": [str(x) for x in got[:n]], "want": want,
            "keyed": keyed, "unreadable": False}
def answer_set(rows, dirs):
    R = [[float(x) for x in r] for r in rows]
    d = [float(x) for x in dirs]
    return [i for i, a in enumerate(R)
            if not any(all((b[c] - a[c]) * d[c] > 0 for c in range(len(d)))
                       for j, b in enumerate(R) if j != i)]


def score_unbeaten_marks(blocks, rows, dirs, yes_word, no_word, labels=None):
    """Score the yes/no marks against the items no other item beats in every column."""
    return verdict(blocks, answer_set(rows, dirs), len(rows), yes_word, no_word, labels)

def record_unbeaten_marks(image, blocks, rows, dirs, yes_word, no_word, labels):
    """Score the item answers and keep the yes/no words and labels used."""
    r = score_unbeaten_marks(blocks, rows, dirs, yes_word, no_word)
    r["yes_word"], r["no_word"] = yes_word, no_word
    r["labels"] = [str(x) for x in (labels or [])]
    return r

# end of code_a23d871dc0aa

# shared code: code_e64078707e2f

import re, difflib


def _c(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def line_coverage(txt, lines):
    s = _c(txt)
    lines = list(lines or [])
    if not lines:
        return 0.0
    ok = 0
    for ln in lines:
        t = _c(ln)
        if not t:
            ok += 1
            continue
        if t in s:
            ok += 1
            continue
        best, n = 0.0, len(t)
        step = max(1, n // 8)
        for i in range(0, max(1, len(s) - n + 1), step):
            best = max(best, difflib.SequenceMatcher(a=t, b=s[i:i + n + 3]).ratio())
        ok += 1 if best >= 0.82 else 0
    return round(ok / float(len(lines)), 4)


def region_text_coverage(rr, lines):
    """Share of the expected text lines found in the text read from the regions."""
    answers = (rr or {}).get('answers') or []
    return line_coverage(" ".join(str(a) for a in answers if a), lines)

# end of code_e64078707e2f

# code: both_ok_code

def separate_and_legible(a, b):
    """Pass only when the items stand separate and the writing is legible."""
    def yes(v):
        return str(v or "").strip().lower().startswith("y")
    ya, yb = yes(a), yes(b)
    return {"frac": 1.0 if (ya and yb) else 0.0, "separate": ya, "legible": yb,
            "verdict": "items separate=%s, writing legible=%s" % (ya, yb)}

# end of both_ok_code
