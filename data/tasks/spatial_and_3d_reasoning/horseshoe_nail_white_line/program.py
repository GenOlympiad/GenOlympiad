# shared code: code_nails
def check_nail_placement(sole, stripe, toe, heads, line, plan):
    """Count nails inside the white line plus branch thirds whose nail count misses the plan."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def word(v, pool):
        s = ' '.join(str(v).strip().lower().split())
        for k in pool:
            if k in s:
                return k
        return None
    def geo(n):
        g = (n or {}).get('geometry') if isinstance(n, dict) else None
        return [b for b in (g or []) if isinstance(b, (list, tuple)) and len(b) >= 4]
    sole_boxes, head_boxes = geo(sole), geo(heads)
    stripe_side = word((lst(stripe) or [''])[0], ('left', 'right'))
    toe_end = word((lst(toe) or [''])[0], ('top', 'bottom'))
    lines = [word(v, ('outside', 'inside')) for v in lst(line)]
    full = sum(plan.values()) + len(plan)
    if not sole_boxes or not head_boxes or stripe_side is None or toe_end is None:
        return {'miss': full, 'n': full,
                'verdict': 'the sole, the stripe side or the toe end could not be read, so '
                           'every check counts against'}
    x0, y0, x1, y1 = [float(v) for v in sole_boxes[0][:4]]
    midx = (x0 + x1) / 2.0
    miss, notes, placed = 0, [], {}
    for i, b in enumerate(head_boxes):
        cx = (float(b[0]) + float(b[2])) / 2.0
        cy = (float(b[1]) + float(b[3])) / 2.0
        s = 'stripe' if ((cx < midx) == (stripe_side == 'left')) else 'other'
        f = (cy - y0) / (y1 - y0) if y1 > y0 else 0.5
        if toe_end == 'bottom':
            f = 1.0 - f
        t = 'front' if f <= 1.0 / 3.0 else ('middle' if f <= 2.0 / 3.0 else 'back')
        l = lines[i] if i < len(lines) else None
        placed[(s, t)] = placed.get((s, t), 0) + 1
        if l != 'outside':
            miss += 1
            notes.append('the nail on the %s branch in the %s third does not read as outside '
                       'the pale band' % (s, t))
        else:
            notes.append('a nail on the %s branch in the %s third, outside the pale band'
                       % (s, t))
    for k, n in sorted(plan.items()):
        key = tuple(k.split('|'))
        if placed.get(key, 0) != n:
            miss += 1
            notes.append('the %s branch %s third holds %d nails, the punching calls for %d'
                       % (key[0], key[1], placed.get(key, 0), n))
    return {'miss': miss, 'n': full, 'verdict': '; '.join(notes) or 'no nail was read'}

# end of code_nails

# shared code: code_clench
def count_clenches_off(row):
    """Count the clenches that stand out of the row instead of level."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def word(v, pool):
        s = ' '.join(str(v).strip().lower().split())
        for k in pool:
            if k in s:
                return k
        return None
    seen = [word(v, ('level', 'off')) for v in lst(row)]
    if not seen or None in seen:
        return {'off': 99, 'n': len(seen),
                'verdict': 'the clenches could not all be read, so none is counted as level'}
    off = sum(1 for v in seen if v == 'off')
    return {'off': off, 'n': len(seen),
            'verdict': '%d of the %d clenches stand out of the row' % (off, len(seen))}

# end of code_clench
