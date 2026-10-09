# shared code: code_ce524948aa7b

import itertools
import re


def _rows(ans):
    if isinstance(ans, (list, tuple)):
        return [str(t).strip().lower() for t in ans]
    return [t.strip().lower() for t in re.split(r"[;\n]+", str(ans or "")) if t.strip()]


def read_times(ans, names):
    want = [str(n).strip().lower() for n in names]
    out = {}
    for chunk in _rows(ans):
        m = re.search(r"(?<![a-z0-9])([a-z])(?![a-z])", chunk)
        nums = re.findall(r"(\d{1,2})\s*[:.]\s*\d{2}|(?<![:.\d])(\d{1,2})(?![:.\d])", chunk)
        vals = [int(a or b) for a, b in nums]
        if m and len(vals) >= 2 and m.group(1) in want and m.group(1) not in out:
            out[m.group(1)] = (vals[0], vals[1])
    return out if len(out) == len(want) else None


def read_marks(ans, names, yes_word):
    want = [str(n).strip().lower() for n in names]
    y = str(yes_word).strip().lower()
    out = {}
    for chunk in _rows(ans):
        m = re.search(r"(?<![a-z0-9])([a-z])(?![a-z])", chunk)
        if not m or m.group(1) not in want or m.group(1) in out:
            continue
        body = chunk[m.end():]
        out[m.group(1)] = (y in body)
    return out if len(out) == len(want) else None


def max_disjoint(ivs):
    names = sorted(ivs)
    for k in range(len(names), 0, -1):
        wits = []
        for combo in itertools.combinations(names, k):
            c = sorted(combo, key=lambda n: ivs[n][0])
            if all(ivs[c[i]][1] <= ivs[c[i + 1]][0] for i in range(len(c) - 1)):
                wits.append(set(combo))
        if wits:
            return k, wits
    return 0, [set()]


def clashes(ivs, chosen):
    out = []
    for a, b in itertools.combinations(sorted(chosen), 2):
        (s1, e1), (s2, e2) = ivs[a], ivs[b]
        if s1 < e2 and s2 < e1:
            out.append([a, b])
    return out


def booking_verdict(times_ans, marks_ans, names, yes_word):
    """Score the ticked bookings against every largest set of non-overlapping bookings."""
    names = [str(n).strip().lower() for n in names]
    intervals = read_times(times_ans, names)
    marks = read_marks(marks_ans, names, yes_word)
    if intervals is None or marks is None:
        return {"unreadable": True, "law": 0.0, "share": 0.0, "feasible": 0.0, "count_ok": 0.0,
                "chosen": None, "best": None}
    best, optimal_sets = max_disjoint(intervals)
    chosen = {n for n in names if marks[n]}
    clash_list = clashes(intervals, chosen)
    share = max(sum(1.0 for n in names if (n in chosen) == (n in w)) / len(names) for w in optimal_sets)
    return {"unreadable": False,
            "law": 1.0 if chosen in optimal_sets else 0.0,
            "share": round(share, 4),
            "feasible": 1.0 if not clash_list else 0.0,
            "count_ok": 1.0 if len(chosen) == best else 0.0,
            "chosen": sorted(chosen), "best": best, "n_optima": len(optimal_sets),
            "clashes": clash_list}

# end of code_ce524948aa7b

# code: cover_code

import difflib
import re


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


def _join(rr):
    if isinstance(rr, dict):
        parts = rr.get('answers') or []
    elif isinstance(rr, (list, tuple)):
        parts = list(rr)
    else:
        parts = [rr]
    keep = []
    for x in parts:
        s = str(x).strip() if x is not None else ''
        if s and s.lower() != 'none':
            keep.append(s)
    return ' '.join(keep)


def cover(reads, lines):
    """The share of expected lines found in the joined read text."""
    text = _join(reads)
    if not text:
        return {'unreadable': True, 'frac': 0.0, 'text': ''}
    return {'unreadable': False, 'frac': line_coverage(text, lines), 'text': text}

# end of cover_code
