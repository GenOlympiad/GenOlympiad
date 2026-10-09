# shared code: code_2c91724486ad

import re


def _clean(tok):
    t = str(tok).strip().strip('*"\'` ').strip()
    t = re.sub(r'^(?:panel\s*)?\d+\s*[.):\-]\s*(?=\S)', '', t, flags=re.I)
    return t.strip().strip('.').strip().casefold()


def _cells(got, k):
    if isinstance(got, dict):
        ans = got.get('answers')
        if isinstance(ans, (list, tuple)) and len(ans) >= k:
            if any(a is None or not str(a).strip() for a in ans[:k]):
                return None
            out = [_clean(a) for a in ans[:k]]
            return out if all(out) else None
        got = ans[0] if ans else None
    if isinstance(got, (list, tuple)):
        out = [_clean(v[0] if isinstance(v, (list, tuple)) and v else v) for v in got]
        return out[:k] if len(out) >= k else None
    if got is None:
        return None
    lines = [l for l in str(got).splitlines() if l.strip()]
    for line in list(reversed(lines)) + [str(got)]:
        toks = [t for t in (_clean(x) for x in line.split(',')) if t]
        if len(toks) >= k:
            return toks[:k]
    return None


def check_lineups(reads, targets):
    """Score 1 when every panel's read coat colour matches the reference sequence."""
    pairs = []
    for got, tgt in zip(reads, targets):
        if tgt is None:
            continue
        tgt = [str(x).strip().casefold() for x in tgt]
        pairs.append((_cells(got, len(tgt)), tgt))
    if not pairs or any(p[0] is None for p in pairs):
        return {"law": 0.0, "share": 0.0, "unreadable": True, "bad": None,
                "verdict": "a panel-attribute read never came back in full -> unreadable"}
    ok = tot = 0
    bad = []
    for gi, (got, tgt) in enumerate(pairs):
        for i, t in enumerate(tgt):
            tot += 1
            if got[i] == t:
                ok += 1
            else:
                bad.append([gi, i + 1, got[i], t])
    return {"law": 1.0 if ok == tot else 0.0, "share": round(ok / tot, 4),
            "unreadable": False, "bad": bad,
            "verdict": "%d/%d panel-cells obey the law -> law %.1f, panel-share %.4f"
                       % (ok, tot, 1.0 if ok == tot else 0.0, ok * 1.0 / tot)}

# end of code_2c91724486ad

# shared code: code_7a2f44a8e527

def panels(na):
    n = int(na)
    rows = 1 if n <= 4 else 2
    cols = n // rows
    inset = 0.04
    cw, ch = 1000.0 / cols, 1000.0 / rows
    ix, iy = inset * cw, inset * ch
    out = []
    for r in range(rows):
        for c in range(cols):
            out.append([round(r * ch + iy, 1), round(c * cw + ix, 1),
                        round((r + 1) * ch - iy, 1), round((c + 1) * cw - ix, 1)])
    return {"boxes": out, "rows": rows, "cols": cols,
            "verdict": "%d panels cut as %d row(s) x %d column(s), reading order, 4 %% inset"
                       % (n, rows, cols)}

# end of code_7a2f44a8e527

# code: panel_reads_code

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


def panel_reads(panel_boxes, panel_confirms, left_reads, right_reads, reference):
    """Read the leftmost and rightmost coat colours of confirmed panels in reading order."""
    items = _reading_order((panel_boxes or {}).get('geometry') or [],
                           (panel_confirms or {}).get('answers') or [],
                           (left_reads or {}).get('answers') or [],
                           (right_reads or {}).get('answers') or [])
    left = [str(v[0]) if v[0] is not None else '' for _b, v in items]
    right = [str(v[1]) if v[1] is not None else '' for _b, v in items]
    return {'left': left, 'right': right, 'n': len(items),
            'verdict': '%d panels confirmed by the ring; in reading order the leftmost coats read '
                       '%s and the rightmost coats read %s' % (len(items), left, right)}

# end of panel_reads_code
