# shared code: code_barb_side
def barb_side_error(name_read, shaft_read, barb_read, names, hemispheres):
    """The worst angle between the barb side read and the side the hemisphere puts barbs on."""
    points = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west',
           'northwest']
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def deg(v):
        w = ''.join(c for c in str(v).lower() if c.isalpha())
        return points.index(w) * 45.0 if w in points else None
    def off(a, b):
        return abs((a - b + 180.0) % 360.0 - 180.0)
    want = [str(k) for k in lst(names)]
    hemisphere_of = [str(h).strip().lower() for h in lst(hemispheres)]
    rows = [{'key': k, 's': s, 'f': f}
            for k, s, f in zip(lst(name_read), lst(shaft_read), lst(barb_read))]
    aligned = align_by_printed_key(rows, want)
    worst, observed, expected, notes = -1.0, 180.0, 0.0, []
    for i, r in enumerate(aligned):
        s = deg(r.get('s')) if isinstance(r, dict) else None
        f = deg(r.get('f')) if isinstance(r, dict) else None
        h = hemisphere_of[i] if i < len(hemisphere_of) else 'either'
        nm_i = want[i] if i < len(want) else str(i)
        if s is None or f is None:
            worst, observed, expected = 180.0, 180.0, 0.0
            notes.append('%s: shaft or barb side not read' % nm_i)
            continue
        if h == 'north':
            candidates = [(s - 90.0) % 360.0]
        elif h == 'south':
            candidates = [(s + 90.0) % 360.0]
        else:
            candidates = [(s - 90.0) % 360.0, (s + 90.0) % 360.0]
        best = candidates[0]
        for c in candidates[1:]:
            if off(f, c) < off(f, best):
                best = c
        error = off(f, best)
        notes.append('%s: shaft %g, barbs %g, hemisphere wants %g, off by %g'
                   % (nm_i, s, f, best, error))
        if error > worst:
            worst, observed, expected = error, f, best
    return {'obs': observed, 'exp': expected, 'worst': worst,
            'verdict': '; '.join(notes) or 'no station plot was read'}

# end of code_barb_side

# shared code: code_shaft_bearing
def shaft_bearing_error(name_read, shaft_read, names, wind_from):
    """The worst angle between each shaft direction read and the reference wind direction."""
    points = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west',
           'northwest']
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def deg(v):
        w = ''.join(c for c in str(v).lower() if c.isalpha())
        return points.index(w) * 45.0 if w in points else None
    def off(a, b):
        return abs((a - b + 180.0) % 360.0 - 180.0)
    want = [str(k) for k in lst(names)]
    targets = lst(wind_from)
    aligned = align_by_printed_key([{'key': k, 's': s}
                                for k, s in zip(lst(name_read), lst(shaft_read))], want)
    worst, observed, expected, notes = -1.0, 180.0, 0.0, []
    for i, r in enumerate(aligned):
        s = deg(r.get('s')) if isinstance(r, dict) else None
        nm_i = want[i] if i < len(want) else str(i)
        try:
            t = float(targets[i]) if i < len(targets) else None
        except (TypeError, ValueError):
            t = None
        if s is None or t is None:
            worst, observed, expected = 180.0, 180.0, 0.0
            notes.append('%s: shaft not read' % nm_i)
            continue
        error = off(s, t)
        notes.append('%s: shaft %g, table wind from %g, off by %g' % (nm_i, s, t, error))
        if error > worst:
            worst, observed, expected = error, s, t
    return {'obs': observed, 'exp': expected, 'worst': worst,
            'verdict': '; '.join(notes) or 'no shaft was read'}

# end of code_shaft_bearing

# shared code: code_cloud_fill
def cloud_fill_matches(name_read, fill_read, names, oktas):
    """Whether every station circle is inked to the fraction its reference cloud oktas call for."""
    steps = ['none of it', 'a quarter', 'a half', 'three quarters', 'all of it']
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def rank(v):
        w = ' '.join(str(v).lower().split())
        for i, s in enumerate(steps):
            if s in w:
                return i
        return None
    def want_rank(o):
        o = int(float(o))
        return 0 if o <= 0 else (1 if o <= 2 else (2 if o <= 4 else (3 if o <= 6 else 4)))
    want = [str(k) for k in lst(names)]
    okta_list = lst(oktas)
    aligned = align_by_printed_key([{'key': k, 'v': v}
                                for k, v in zip(lst(name_read), lst(fill_read))], want)
    seen, bad, notes = 0, [], []
    for i, r in enumerate(aligned):
        g = rank(r.get('v')) if isinstance(r, dict) else None
        nm_i = want[i] if i < len(want) else str(i)
        try:
            w = want_rank(okta_list[i]) if i < len(okta_list) else None
        except (TypeError, ValueError):
            w = None
        if g is None or w is None:
            bad.append(nm_i)
            notes.append('%s: inked fraction not read' % nm_i)
            continue
        seen += 1
        if g != w:
            bad.append(nm_i)
        notes.append('%s: inked %s, table wants %s' % (nm_i, steps[g], steps[w]))
    good = seen > 0 and seen == len(want) and not bad
    return {'state': 'match' if good else 'mismatch', 'n': seen,
            'verdict': '; '.join(notes) + ' | wrong: ' + (' '.join(bad) or 'none')}

# end of code_cloud_fill
