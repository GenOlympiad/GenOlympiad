# code: helpers
from genolympiad.task_helpers import to_float
# end of helpers

# shared code: code_6af77f3ee692

import re


def _clean(w):
    return re.sub(r"[^a-z]", "", str(w).lower())


def _words(s):
    return [w for w in (_clean(t) for t in re.split(r"\s+", str(s).strip())) if w]


def _split_rows(ans):
    if not ans:
        return []
    txt = str(ans).strip()
    for fence in ("```", "'" * 3):
        if txt.startswith(fence):
            txt = txt.strip(fence).strip()
    return [p.strip() for p in re.split(r"[|\n]", txt) if p.strip()]


_TAG = re.compile(r"^\s*[\(\[]?\s*(\d{1,2})\s*([ABab])\s*[:.\)\-]\s*(.*)$")


def _tagged_pairs(ans, n):
    A, B = {}, {}
    for field in _split_rows(ans):
        m = _TAG.match(field)
        if not m:
            continue
        (A if m.group(2).upper() == "A" else B)[int(m.group(1))] = m.group(3).strip()
    n = int(n)
    if any(i not in A or i not in B for i in range(1, n + 1)):
        return None
    return [(A[i], B[i]) for i in range(1, n + 1)]


def _rowend(row):
    a = str(row).strip().lower().rstrip(" .,;:")
    return re.sub(r"\s+-\s*$", "-", a)


def _rowstart(row):
    return str(row).strip().lower().lstrip(" \"'“‘")


def _out(n_bad, n_units, unreadable=False, note=""):
    if unreadable:
        return {"unreadable": 1.0, "ok": 0.0, "frac": 0.0, "bad": -1.0, "n": 0.0, "note": note}
    n_units = max(1, int(n_units))
    n_bad = max(0, int(n_bad))
    return {"unreadable": 0.0, "ok": (1.0 if n_bad == 0 else 0.0),
            "frac": max(0.0, (n_units - n_bad) / float(n_units)),
            "bad": float(n_bad), "n": float(n_units), "note": note}

def breaks_at_required_point(ans, n_entries, words, cuts, min_words):
    """Score entries broken at the required point with a hyphen and enough words."""
    pairs = _tagged_pairs(ans, n_entries)
    if pairs is None:
        return _out(0, 0, unreadable=True,
                    note="tagged rows did not come back for all %d entries" % int(n_entries))
    bad = 0
    for i, (ra, rb) in enumerate(pairs):
        w = _clean(words[i])
        c = int(cuts[i])
        nw = len(_words(ra)) + len(_words(rb)) - 1
        if (not _rowend(ra).endswith(w[:c] + "-")
                or not _rowstart(rb).startswith(w[c:])
                or nw < int(min_words)):
            bad += 1
    return _out(bad, int(n_entries), note="entries=%d" % int(n_entries))


def two_row_breaks(ans, n_entries):
    """Score entries whose first row ends in a hyphen and whose second row has words."""
    pairs = _tagged_pairs(ans, n_entries)
    if pairs is None:
        return _out(0, 0, unreadable=True,
                    note="tagged rows did not come back for all %d entries" % int(n_entries))
    bad = 0
    for ra, rb in pairs:
        if not _rowend(ra).endswith("-") or not _words(rb):
            bad += 1
    return _out(bad, int(n_entries), note="two-row breaks")

# end of code_6af77f3ee692
