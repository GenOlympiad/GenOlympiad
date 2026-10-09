# shared code: code_9aafcd355177

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
def answer_set(rows, direction):
    R = [[float(x) * float(direction) for x in r] for r in rows]
    win = set()
    for c in range(len(R[0])):
        best = max(R[i][c] for i in range(len(R)))
        win |= {i for i in range(len(R)) if R[i][c] == best}
    return [i for i in range(len(R)) if i not in win]


def score_rows(blocks, rows, direction, yes_word, no_word, labels=None):
    """Score the read rows against the rows that should carry the yes word."""
    return verdict(blocks, answer_set(rows, direction), len(rows), yes_word, no_word, labels)

def score_rows_with_labels(image, blocks, rows, direction, yes_word, no_word, labels):
    """Score the read rows and keep the yes and no words and labels for display."""
    r = score_rows(blocks, rows, direction, yes_word, no_word)
    r["yes_word"], r["no_word"] = yes_word, no_word
    r["labels"] = [str(x) for x in (labels or [])]
    return r

# end of code_9aafcd355177

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


def region_text_coverage(region_reads, lines):
    """Share of the expected lines found in the text read across all regions."""
    answers = (region_reads or {}).get('answers') or []
    return line_coverage(" ".join(str(a) for a in answers if a), lines)

# end of code_e64078707e2f

# code: both_ok_code

def separate_and_legible(a, b):
    """Score 1 only if the items are separate and the writing is legible."""
    def yes(v):
        return str(v or "").strip().lower().startswith("y")
    ya, yb = yes(a), yes(b)
    return {"frac": 1.0 if (ya and yb) else 0.0, "separate": ya, "legible": yb,
            "verdict": "items separate=%s, writing legible=%s" % (ya, yb)}

# end of both_ok_code
