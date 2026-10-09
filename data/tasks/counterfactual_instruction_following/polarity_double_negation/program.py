# shared code: code_20e584ed882c

import re


def _tok(a):
    return re.sub(r'[^a-z0-9]', '', str(a).lower())


def _num(a):
    m = re.findall(r'-?\d+', str(a))
    return None if not m else int(m[-1])


def m1(a, k, kind):
    if a is None:
        return 0.0
    if kind == 'num':
        v = _num(a)
        return 1.0 if (v is not None and v == int(k)) else 0.0
    if kind == 'hour':
        v = _num(a)
        return 1.0 if (v is not None and v % 12 == int(k) % 12) else 0.0
    if kind == 'time':
        ds = re.sub(r'[^0-9]', '', str(a))
        dk = re.sub(r'[^0-9]', '', str(k))
        if not dk or not ds:
            return 0.0
        return 1.0 if ds.zfill(4) == dk.zfill(4) else 0.0
    return 1.0 if _tok(a) == _tok(k) else 0.0


def _pairs(seq, targets, kinds):
    out = []
    for i, k in enumerate(targets):
        kind = kinds[i] if i < len(kinds) else 'eq'
        a = seq[i] if (isinstance(seq, (list, tuple)) and i < len(seq)) else None
        out.append(m1(a, k, kind))
    return out


def count_seq(seq, targets, kinds):
    if not isinstance(seq, (list, tuple)) or len(seq) < len(targets):
        return 0.0
    return 1.0 if all(v >= 1.0 for v in _pairs(seq, targets, kinds)) else 0.0


def agree_seq(seq, targets, kinds):
    if not targets:
        return 0.0
    return round(sum(_pairs(seq, targets, kinds)) / len(targets), 4)


def _norm(e, kind):
    if kind != "eq":
        return e
    import re as _re
    w = _re.findall(r"[A-Za-z]+", str(e))
    return w[-1] if w else e


def _items(r, n):
    if isinstance(r, dict) or not isinstance(r, (list, tuple)) or len(r) < int(n):
        return None
    return [(" ".join(str(x) for x in v) if isinstance(v, (list, tuple)) else str(v))
            for v in list(r)[:int(n)]]


def _weave(ra, rb, n):
    a, b = _items(ra, n), _items(rb, n)
    if a is None or b is None:
        return None
    out = []
    for i in range(int(n)):
        out.append(a[i])
        out.append(b[i])
    return out


def _refused(targets):
    return {"frac": 0.0, "unreadable": True, "read": None, "want": list(targets),
            "verdict": "an ordered single-fact read did not come back complete -> honest refusal"}


def sequence_all_match(ra, rb, targets, kinds):
    """Interleave the colour and name reads; full marks only if every entry matches."""
    seq = _weave(ra, rb, len(targets) // 2)
    if seq is None:
        return _refused(targets)
    seq = [_norm(e, kinds[i] if i < len(kinds) else "eq") for i, e in enumerate(seq)]
    f = count_seq(seq, targets, kinds)
    return {"frac": f, "unreadable": False, "read": seq, "want": list(targets),
            "verdict": "read %s vs required %s -> %s"
                       % (seq, list(targets), "MATCH" if f >= 1.0 else "MISMATCH")}


def sequence_agreement(ra, rb, targets, kinds):
    """Interleave the colour and name reads and give the share of entries that match."""
    seq = _weave(ra, rb, len(targets) // 2)
    if seq is None:
        return _refused(targets)
    seq = [_norm(e, kinds[i] if i < len(kinds) else "eq") for i, e in enumerate(seq)]
    a = agree_seq(seq, targets, kinds)
    return {"frac": a, "unreadable": False, "read": seq, "want": list(targets),
            "verdict": "positional agreement %s (read %s vs required %s)"
                       % (a, seq, list(targets))}

# end of code_20e584ed882c

# shared code: code_e1be18a17f73

def group_count(n, per):
    """The sequence length divided by the group size, at least one."""
    return max(1, int(n) // int(per))

# end of code_e1be18a17f73

# code: order_code

def samples_in_reading_order(sample_boxes, sample_confirms, colour_reads, name_reads, n_cards):
    """Put the confirmed samples in reading order and list their colours and names."""
    def cy(b):
        return (float(b[0]) + float(b[2])) / 2.0

    def cx(b):
        return (float(b[1]) + float(b[3])) / 2.0

    def hh(b):
        return abs(float(b[2]) - float(b[0]))

    def yes(a):
        return str(a).strip().lower().startswith('y')

    geometry = (sample_boxes or {}).get('geometry') or []
    ok = (sample_confirms or {}).get('answers') or []
    colours = (colour_reads or {}).get('answers') or []
    names = (name_reads or {}).get('answers') or []
    cards = []
    for i in range(min(len(geometry), len(ok))):
        if not yes(ok[i]):
            continue
        cards.append({'box': geometry[i],
                      'colour': colours[i] if i < len(colours) else None,
                      'name': names[i] if i < len(names) else None})
    cards.sort(key=lambda c: cy(c['box']))
    rows, cur = [], []
    for c in cards:
        if not cur:
            cur = [c]
            continue
        gap = abs(cy(c['box']) - cy(cur[-1]['box']))
        if gap < 0.5 * max(hh(c['box']), hh(cur[-1]['box'])):
            cur.append(c)
        else:
            rows.append(cur)
            cur = [c]
    if cur:
        rows.append(cur)
    ordered = []
    for r in rows:
        ordered.extend(sorted(r, key=lambda c: cx(c['box'])))
    return {'colours': [c['colour'] for c in ordered],
            'names': [c['name'] for c in ordered],
            'n': len(ordered), 'want': int(n_cards),
            'verdict': '%d cards confirmed by the ring (the picture was asked for %d); in '
                       'reading order their painted blocks read %s and their printed names read %s'
                       % (len(ordered), int(n_cards),
                          [str(c['colour']) for c in ordered],
                          [str(c['name']) for c in ordered])}

# end of order_code

# code: hold_count_seq_code
def hold_count_seq(r):
    """Set refused when the all-match read was unreadable, so the task is withheld."""
    d = dict(r or {})
    if d.get('unreadable'):
        d['refused'] = True
    return d

# end of hold_count_seq_code

# code: hold_agreement_seq_code
def hold_agreement_seq(r):
    """Set refused when the agreement read was unreadable, so the task is withheld."""
    d = dict(r or {})
    if d.get('unreadable'):
        d['refused'] = True
    return d

# end of hold_agreement_seq_code

# code: page_cov_code

import re, difflib


def _c(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower())


def cov(txt, lines):
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
        best = 0.0
        n = len(t)
        step = max(1, n // 8)
        for i in range(0, max(1, len(s) - n + 1), step):
            best = max(best, difflib.SequenceMatcher(a=t, b=s[i:i + n + 3]).ratio())
        ok += 1 if best >= 0.82 else 0
    return round(ok / len(lines), 4)


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


def page_text_coverage(lines, *reads):
    """Share of expected lines found in the joined strip reads, refusing when none read."""
    s = _strip_texts(*reads)
    if not _c(s):
        return {"frac": 0.0, "no_read": True, "refused": True,
                "verdict": "no strip returned any readable text -> honest refusal"}
    r = cov(s, lines)
    if isinstance(r, dict):
        d = dict(r)
        d["no_read"] = False
        d["page_text"] = s
        return d
    return {"frac": r, "no_read": False, "page_text": s}

# end of page_cov_code
