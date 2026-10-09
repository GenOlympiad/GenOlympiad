# shared code: code_80ab5ae8be96
def level_matches(value, target):
    """Score 1 if the level read is within 0.5 of the reference level."""
    try:
        return 1.0 if abs(float(value) - float(target)) <= 0.5 else 0.0
    except Exception:
        return 0.0

# end of code_80ab5ae8be96

# code: bridge_ok_code
def columns_bridge(cols, confirm_read):
    """Whether each confirmed column starts within tolerance of where the previous one ends."""
    boxes = [g for g, a in zip((cols or {}).get('geometry') or [],
                           (confirm_read or {}).get('answers') or [])
         if str(a).strip().lower().startswith('y')]
    if len(boxes) < 2:
        return {'value': 'no', 'n': len(boxes), 'why': 'fewer than two columns confirmed'}
    boxes = sorted(boxes, key=lambda g: g[1] + g[3])
    tolerance = 0.03 * (max(g[2] for g in boxes) - min(g[0] for g in boxes))
    offsets = [min(abs(p - q) for p in (a[0], a[2]) for q in (c[0], c[2]))
           for a, c in zip(boxes, boxes[1:])]
    return {'value': ('yes' if max(offsets) <= tolerance else 'no'), 'n': len(boxes),
            'worst': round(max(offsets), 1), 'tol': round(tolerance, 1)}

# end of bridge_ok_code

# code: chain_code
def running_total_share(cols, vals, levels):
    """The share of running totals read left to right that match the reference levels."""
    import re
    boxes = [[float(v) for v in b] for b in ((cols or {}).get('geometry') or [])]
    answers = list((vals or {}).get('answers') or [])
    if not boxes or len(boxes) != len(answers):
        return {'frac': 0.0, 'read': None, 'unreadable': True}
    order = sorted(range(len(boxes)), key=lambda i: (boxes[i][1] + boxes[i][3]) / 2.0)
    totals = []
    for i in order:
        m = re.search(r'-?\d+', str(answers[i]).replace(',', ''))
        if not m:
            return {'frac': 0.0, 'read': None, 'unreadable': True}
        totals.append(int(m.group(0)))
    want = list(levels or [])
    if len(totals) != len(want):
        return {'frac': 0.0, 'read': totals, 'want': want, 'unreadable': False,
                'note': 'the chart prints %d running totals, the chain has %d'
                        % (len(totals), len(want))}
    n_match = sum(1 for a, b in zip(totals, want) if a == b)
    return {'frac': round(n_match * 1.0 / len(want), 4), 'read': totals, 'want': want,
            'matched': n_match, 'unreadable': False}

# end of chain_code
