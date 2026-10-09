# code: read_columns_code

def read_dot_columns(column_boxes, column_confirms, dot_boxes, dot_confirms, dot_reads, reference):
    """Read which dots are filled in each of the three confirmed dot columns, left to right."""
    def cy(b):
        return (float(b[0]) + float(b[2])) / 2.0

    def cx(b):
        return (float(b[1]) + float(b[3])) / 2.0

    def inside(p, b):
        return (float(b[0]) <= cy(p) <= float(b[2])) and (float(b[1]) <= cx(p) <= float(b[3]))

    def yes(a):
        return str(a).strip().lower().startswith('y')

    def filled(a):
        t = str(a).strip().lower()
        if 'empty' in t or 'outline' in t or 'hollow' in t or 'unfilled' in t:
            return False
        if 'fill' in t or 'solid' in t:
            return True
        return None

    def phrase(p):
        names = [n for n, f in zip(('top', 'middle', 'bottom'), p) if f]
        if not names:
            return 'none'
        if len(names) == 1:
            return names[0]
        return '%s and %s' % (', '.join(names[:-1]), names[-1])

    cg = (column_boxes or {}).get('geometry') or []
    ca = (column_confirms or {}).get('answers') or []
    cols = [cg[i] for i in range(min(len(cg), len(ca))) if yes(ca[i])]
    cols.sort(key=cx)

    dg = (dot_boxes or {}).get('geometry') or []
    da = (dot_confirms or {}).get('answers') or []
    dvv = (dot_reads or {}).get('answers') or []
    dots = []
    for i in range(min(len(dg), len(da))):
        if not yes(da[i]):
            continue
        dots.append({'box': dg[i], 'filled': filled(dvv[i] if i < len(dvv) else None)})

    result = {'n_cols': len(cols), 'n_dots': len(dots), 'c1': None, 'c2': None, 'c3': None}
    if len(cols) != 3:
        result['verdict'] = ('%d large dot columns were confirmed one at a time, but the card was '
                          'asked for 3, so the coded word cannot be read off'
                          % len(cols))
        return result

    groups = [[] for _ in cols]
    loose = 0
    for d in dots:
        hit = [j for j in range(3) if inside(d['box'], cols[j])]
        if not hit:
            loose += 1
            continue
        groups[hit[0]].append(d)

    out = []
    for j in range(3):
        g = groups[j]
        pat = [0, 0, 0]
        if len(g) == 3:
            g = sorted(g, key=lambda d: cy(d['box']))
            slots = [0, 1, 2]
        else:
            y0, y1 = float(cols[j][0]), float(cols[j][2])
            span = max(y1 - y0, 1e-6)
            slots = []
            for d in g:
                k = int(3.0 * (cy(d['box']) - y0) / span)
                slots.append(min(max(k, 0), 2))
            if len(set(slots)) != len(slots):
                out.append(None)
                continue
        bad = False
        for d, k in zip(g, slots):
            if d['filled'] is None:
                bad = True
                break
            pat[k] = 1 if d['filled'] else 0
        out.append(None if bad else phrase(pat))

    result['c1'], result['c2'], result['c3'] = out[0], out[1], out[2]
    result['loose_dots'] = loose
    result['verdict'] = ('3 large dot columns and %d dot places were confirmed one at a time; left '
                      'to right the columns hold a filled dot at: %s'
                      % (len(dots), ' | '.join(str(x) for x in out)))
    return result

# end of read_columns_code

# code: wchk_code
def word_matches_reference(g1, g2, g3, want):
    """Decode the three dot patterns into letters and score 1 if they spell the word."""
    pattern_letter = {(1,0,0):'c',(0,1,0):'a',(0,0,1):'t',(1,1,0):'r',(0,1,1):'n',(1,0,1):'s',(1,1,1):'o'}
    def pat(ans):
        if ans is None or isinstance(ans, dict): return None
        t = ' ' + __import__('re').sub(r'[^a-z0-9]+', ' ', str(ans).lower()).strip() + ' '
        if 'none' in t or 'no dot' in t: return (0,0,0)
        if 'all' in t: return (1,1,1)
        return (1 if 'top' in t else 0, 1 if 'mid' in t else 0, 1 if 'bottom' in t else 0)
    letters = []
    for a in (g1, g2, g3):
        p = pat(a)
        if p is None or p not in pattern_letter: return 0.0
        letters.append(pattern_letter[p])
    return 1.0 if ''.join(letters) == str(want).strip().lower() else 0.0

# end of wchk_code
