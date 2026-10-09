# shared code: code_cross
def check_crossings(disc_keys, line_reads, break_reads, width_reads, plan):
    """Count crossings whose line, break and width reads differ from the floor plan."""
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
        return ''.join(c for c in str(v).upper() if c.isalnum())
    want = sorted(plan.keys())
    rows = [{'key': key(a), 'a': b, 'b': c, 'c': d}
            for a, b, c, d in zip(lst(disc_keys), lst(line_reads), lst(break_reads), lst(width_reads))]
    got = align_by_printed_key(rows, want)
    miss, say = 0, []
    for i, k in enumerate(want):
        r = got[i] if i < len(got) else None
        a = word(r.get('a'), ('walkway', 'aisle', 'outline')) if isinstance(r, dict) else None
        b = word(r.get('b'), ('broken', 'unbroken')) if isinstance(r, dict) else None
        c = word(r.get('c'), ('same', 'wider')) if isinstance(r, dict) else None
        w = plan[k]
        if [a, b, c] == list(w):
            say.append('%s: %s, %s, %s -- as it should be' % (k, a, b, c))
        else:
            miss += 1
            say.append('%s: read %s, %s, %s; it should be %s, %s, %s'
                       % (k, a, b, c, w[0], w[1], w[2]))
    return {'miss': miss, 'n': len(want), 'verdict': '; '.join(say) or 'nothing was read'}

# end of code_cross

# shared code: code_discs
def read_disc_labels(disc_reads):
    """List the inspection disc labels read back, in reading order."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    seen, say = [], []
    for v in lst(disc_reads):
        s = ' '.join(str(v).strip().upper().split())
        if s:
            seen.append(s)
            say.append('read %s' % s)
    return {'seen': seen, 'n': len(seen), 'verdict': '; '.join(say) or 'nothing was read'}

# end of code_discs
