# code: bands_code
def top_slices(sign_boxes, frac=0.20):
    """Cut the top fifth of each confirmed sign box as its top strip."""
    g = (sign_boxes or {}).get('geometry') or []
    top = []
    for b in g:
        try:
            y0, x0, y1, x1 = [float(v) for v in list(b)[:4]]
        except (TypeError, ValueError):
            continue
        if y1 <= y0 or x1 <= x0:
            continue
        top.append([y0, x0, y0 + frac * (y1 - y0), x1])
    return {'top': top, 'n': len(top), 'frac': frac,
            'note': ('%d confirmed sign box(es) -> %d top slice(s), each the top %.0f%% of its '
                     'own box' % (len(g), len(top), frac * 100))}

# end of bands_code

# code: headcount_code
def m(ans, key):
    if ans is None:
        return 0.0
    import re
    a = str(ans).strip().lower()
    k = str(key).strip().lower()
    opp = 'up' if k == 'down' else 'down'
    toks = re.findall(r'[a-z]+', a)
    if opp in toks and k not in toks:
        return 0.0
    return 1.0 if k in toks else (0.0 if opp in a else (1.0 if k in a else 0.0))


def orient(ans):
    import re
    if ans is None:
        return None
    toks = re.findall(r'[a-z]+', str(ans).lower())
    across = ('across' in toks) or ('all' in toks and 'way' in toks)
    narrow = ('narrow' in toks) or ('middle' in toks)
    if across == narrow:
        return None
    return 'down' if across else 'up'


def score_sign_orientation(strip_reads, expects, n_demanded):
    """Full credit only if the count matches and every top strip shows the demanded way up."""
    answers = (strip_reads or {}).get('answers') or []
    n_items = len(answers)
    try:
        n_demanded = int(n_demanded)
    except (TypeError, ValueError):
        n_demanded = -1
    if n_items == 0:
        return {'frac': 0.0, 'n_items': 0, 'n_ok': 0, 'n_want': n_demanded, 'reads': [],
                'verdict': 'no counted object survived the box acceptance gate -> frac 0.0'}
    reads, n_amb = [], 0
    for i, a in enumerate(answers):
        o = orient(a)
        if o is None:
            n_amb += 1
        reads.append({'i': i, 'top_strip': a, 'apex': o or 'ambiguous'})
    n_ok = int(sum(1 for r in reads if m(r['apex'], expects) >= 1.0))
    if n_items != n_demanded:
        return {'frac': 0.0, 'n_items': n_items, 'n_ok': n_ok, 'n_want': n_demanded, 'reads': reads,
                'verdict': ('the count found %d confirmed object(s), the prompt demanded %d '
                            '-> frac 0.0' % (n_items, n_demanded))}
    frac = 1.0 if n_ok == n_items else 0.0
    return {'frac': frac, 'n_items': n_items, 'n_ok': n_ok, 'n_want': n_demanded, 'reads': reads,
            'verdict': ('%d of %d objects read "%s" from their own top strip (%d ambiguous) '
                        '-> frac %.1f' % (n_ok, n_items, str(expects), n_amb, frac))}

# end of headcount_code
