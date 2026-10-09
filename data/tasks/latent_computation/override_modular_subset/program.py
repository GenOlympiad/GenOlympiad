# shared code: code_c6204e3f6eb3

import re


def _tok(a):
    return re.sub(r"[^a-z0-9]", "", str(a).lower())


def _num(a):
    m = re.findall(r"-?\d+", str(a))
    return None if not m else int(m[-1])


def _one(a, k, kind):
    if a is None:
        return 0.0
    if isinstance(a, (list, tuple)):
        a = a[0] if a else None
    if kind == "num":
        v = _num(a)
        return 1.0 if (v is not None and v == int(k)) else 0.0
    if kind == "score":
        ds = re.findall(r"\d+", str(a))
        dk = re.findall(r"\d+", str(k))
        return 1.0 if (len(ds) >= 2 and len(dk) >= 2 and ds[:2] == dk[:2]) else 0.0
    s, t = _tok(a), _tok(k)
    if not t:
        return 0.0
    return 1.0 if (s == t or (len(t) >= 3 and t in s)) else 0.0


def _slots(got, want, kind):
    if isinstance(want, (list, tuple)):
        if isinstance(got, dict) or not isinstance(got, (list, tuple)) or len(got) < len(want):
            return None
        return [_one(got[i], w, kind) for i, w in enumerate(want)]
    if got is None or isinstance(got, dict):
        return None
    return [_one(got, want, kind)]


def score_slots(gots, wants, kinds):
    """1.0 when every read slot matches its expected value, with the share matched."""
    slots = []
    for g, w, k in zip(gots, wants, kinds):
        s = _slots(g, w, k)
        if s is None:
            return {"law": 0.0, "share": 0.0, "unreadable": True}
        slots += s
    if not slots:
        return {"law": 0.0, "share": 0.0, "unreadable": True}
    ok = sum(slots)
    return {"law": 1.0 if ok == len(slots) else 0.0,
            "share": round(ok / float(len(slots)), 4), "unreadable": False}

# end of code_c6204e3f6eb3

# code: door_slots_code

def _cx(b):
    return (float(b[1]) + float(b[3])) / 2.0


def _cy(b):
    return (float(b[0]) + float(b[2])) / 2.0


def _yes(a):
    return str(a).strip().lower().startswith('y')


def _reading_order(geo, ok, *cols):
    items = []
    for i in range(min(len(geo), len(ok))):
        if not _yes(ok[i]):
            continue
        items.append((geo[i], [(c[i] if i < len(c) else None) for c in cols]))
    items.sort(key=lambda it: _cy(it[0]))
    rows, cur = [], []
    for it in items:
        if cur and abs(_cy(it[0]) - _cy(cur[-1][0])) >= 0.5 * max(
                abs(float(it[0][2]) - float(it[0][0])),
                abs(float(cur[-1][0][2]) - float(cur[-1][0][0]))):
            rows.append(cur)
            cur = []
        cur.append(it)
    if cur:
        rows.append(cur)
    out = []
    for r in rows:
        out.extend(sorted(r, key=lambda it: _cx(it[0])))
    return out


def door_slots(box_node, confirm_node, number_node, word_node, reference):
    """Read each confirmed mailbox as its number and word, in reading order."""
    import re
    items = _reading_order((box_node or {}).get('geometry') or [],
                           (confirm_node or {}).get('answers') or [],
                           (number_node or {}).get('answers') or [],
                           (word_node or {}).get('answers') or [])
    slots = []
    for _b, v in items:
        m = re.search(r'-?\d+(?:\.\d+)?', str(v[0] if v[0] is not None else ''))
        num = m.group() if m else ''
        words = re.findall(r'[A-Za-z]+', str(v[1] if v[1] is not None else ''))
        word = words[-1].upper() if words else ''
        slots.append(('%s %s' % (num, word)).strip())
    return {'slots': slots, 'n': len(slots),
            'verdict': '%d carriers confirmed by the ring; left to right they read %s'
                       % (len(slots), slots)}

# end of door_slots_code

# code: page_cov_code

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


def _strip_texts(*rs):
    out = []
    for r in rs:
        if isinstance(r, dict):
            for a in (r.get("answers") or []):
                if a:
                    out.append(str(a))
        elif r:
            out.append(str(r))
    return " ".join(out)


def page_line_coverage(lines, *strip_reads):
    """The share of expected page lines found in the text read from the strips."""
    s = _strip_texts(*strip_reads)
    if not _c(s):
        return {"frac": 0.0, "no_read": True,
                "verdict": "no strip returned any readable text -> honest refusal"}
    r = line_coverage(s, lines)
    if isinstance(r, dict):
        d = dict(r)
        d["no_read"] = False
        d["page_text"] = s
        return d
    return {"frac": r, "no_read": False, "page_text": s}

# end of page_cov_code
