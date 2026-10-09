# shared code: code_overlap_hand
def check_placket_overlap(style_reads, top_reads, hole_reads, styles, sides):
    """Match if each garment's top ply is on the expected side with buttonholes on that side."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def side(v):
        w = str(v).strip().lower()
        if 'left' in w:
            return 'left'
        if 'right' in w:
            return 'right'
        return None
    def key(v):
        return ''.join(c for c in str(v) if c.isdigit())
    want = [key(s) for s in lst(styles)]
    expected_sides = [str(s).strip().lower() for s in lst(sides)]
    rows = [{'key': key(k), 't': t, 'h': h}
            for k, t, h in zip(lst(style_reads), lst(top_reads), lst(hole_reads))]
    got = align_by_printed_key(rows, want)
    seen, bad, say = 0, [], []
    for i, r in enumerate(got):
        t = side(r.get('t')) if isinstance(r, dict) else None
        h = side(r.get('h')) if isinstance(r, dict) else None
        e = expected_sides[i] if i < len(expected_sides) else None
        k = want[i] if i < len(want) else str(i)
        if t is None or h is None or e is None:
            bad.append(k)
            say.append('%s: not read' % k)
            continue
        seen += 1
        if t != e or h != t:
            bad.append(k)
        say.append('%s: top ply %s (class wants %s), buttonholes %s' % (k, t, e, h))
    good = seen > 0 and seen == len(want) and not bad
    return {'state': 'match' if good else 'mismatch', 'n': seen,
            'verdict': '; '.join(say) + ' | wrong: ' + (' '.join(bad) or 'none')}

# end of code_overlap_hand

# shared code: code_button_ply
def check_button_side(style_reads, top_reads, button_reads, styles):
    """Match if each garment's buttons sit on the side opposite its top ply."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def side(v):
        w = str(v).strip().lower()
        if 'left' in w:
            return 'left'
        if 'right' in w:
            return 'right'
        return None
    def key(v):
        return ''.join(c for c in str(v) if c.isdigit())
    want = [key(s) for s in lst(styles)]
    rows = [{'key': key(k), 't': t, 'b': b}
            for k, t, b in zip(lst(style_reads), lst(top_reads), lst(button_reads))]
    got = align_by_printed_key(rows, want)
    seen, bad, say = 0, [], []
    for i, r in enumerate(got):
        t = side(r.get('t')) if isinstance(r, dict) else None
        b = side(r.get('b')) if isinstance(r, dict) else None
        k = want[i] if i < len(want) else str(i)
        if t is None or b is None:
            bad.append(k)
            say.append('%s: not read' % k)
            continue
        seen += 1
        if b == t:
            bad.append(k)
        say.append('%s: top ply %s, buttons %s' % (k, t, b))
    good = seen > 0 and seen == len(want) and not bad
    return {'state': 'match' if good else 'mismatch', 'n': seen,
            'verdict': '; '.join(say) + ' | wrong: ' + (' '.join(bad) or 'none')}

# end of code_button_ply
