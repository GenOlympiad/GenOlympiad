# shared code: code_facing
def worst_cut_facing(tag_reads, lie_reads, cut_reads, plan):
    """The worst angle between each shoot's lie and the way its cut faces, read as clock hours."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def hour(v):
        d = ''.join(c for c in str(v) if c.isdigit())
        try:
            h = int(d)
        except (TypeError, ValueError):
            return None
        return (h % 12) * 30.0 if 1 <= h <= 12 else None
    def key(v):
        return ''.join(c for c in str(v) if c.isdigit())
    want = sorted(plan.keys())
    rows = [{'key': key(a), 'l': b, 'c': c} for a, b, c in zip(lst(tag_reads), lst(lie_reads), lst(cut_reads))]
    aligned = align_by_printed_key(rows, want)
    worst, notes = 0.0, []
    for i, k in enumerate(want):
        r = aligned[i] if i < len(aligned) else None
        l = hour(r.get('l')) if isinstance(r, dict) else None
        c = hour(r.get('c')) if isinstance(r, dict) else None
        if l is None or c is None:
            worst = 180.0
            notes.append('shoot %s: the board could not be read, so the worst error is taken' % k)
            continue
        d = abs((c - l + 180.0) % 360.0 - 180.0)
        worst = max(worst, d)
        notes.append('shoot %s lies toward %g degrees and its cut faces %g, %g apart'
                   % (k, l, c, d))
    if not want:
        worst = 180.0
    return {'worst': worst, 'n': len(want),
            'verdict': '; '.join(notes) or 'no shoot was read'}

# end of code_facing

# shared code: code_bud
def count_bud_misses(label_reads, position_reads, facing_reads, plan):
    """Count shoots not cut just above an outward bud as the plan wants."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def word(v, pool):
        s = ' '.join(str(v).strip().lower().split())
        for k in sorted(pool, key=len, reverse=True):
            if k in s:
                return k
        return None
    def key(v):
        return ' '.join(str(v).strip().upper().split())
    want = sorted(plan.keys())
    rows = [{'key': key(a), 'a': b, 'b': c} for a, b, c in zip(lst(label_reads), lst(position_reads), lst(facing_reads))]
    aligned = align_by_printed_key(rows, want)
    miss, notes = 0, []
    for i, k in enumerate(want):
        r = aligned[i] if i < len(aligned) else None
        a = word(r.get('a'), ('below', 'elsewhere')) if isinstance(r, dict) else None
        b = word(r.get('b'), ('outward', 'inward')) if isinstance(r, dict) else None
        w = plan[k]
        if [a, b] == list(w):
            notes.append('%s: %s and %s -- as it should be' % (k, a, b))
        else:
            miss += 1
            notes.append('%s: read %s and %s; it should be %s and %s'
                       % (k, a, b, w[0], w[1]))
    return {'miss': miss, 'n': len(want), 'verdict': '; '.join(notes) or 'nothing was read'}

# end of code_bud
