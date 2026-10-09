# shared code: code_race
def check_race_sides(peg_numbers, side_reads, shape_reads, peg_plan):
    """Count pegs where the race side and shape differ from the plan: solid on curves, open on straights."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def norm(v):
        return ' '.join(str(v).strip().lower().split())
    def word(v, pool):
        s = norm(v)
        for k in pool:
            if k in s:
                return k
        return None
    plan = dict((norm(k), v) for k, v in (peg_plan or {}).items())
    rows = [{'key': norm(k), 'w': w, 'c': c}
            for k, w, c in zip(lst(peg_numbers), lst(side_reads), lst(shape_reads))]
    got = align_by_printed_key(rows, list(plan.keys()))
    n_wrong, say = 0, []
    for i, k in enumerate(plan.keys()):
        r = got[i] if i < len(got) else None
        w = word(r.get('w'), ('solid', 'open')) if isinstance(r, dict) else None
        c = word(r.get('c'), ('curve', 'straight')) if isinstance(r, dict) else None
        want_c = 'curve' if plan[k] == 'curved' else 'straight'
        want_w = 'solid' if plan[k] == 'curved' else 'open'
        if w == want_w and c == want_c:
            say.append('peg %s: %s side on a %s length, as planned' % (k, w, c))
        else:
            n_wrong += 1
            say.append('peg %s: read %s side on a %s length, plan wants %s on a %s length'
                       % (k, w, c, want_w, want_c))
    return {'miss': n_wrong, 'n': len(plan), 'verdict': '; '.join(say) or 'no peg was read'}

# end of code_race

# shared code: code_pegs
def read_peg_numbers(peg_numbers):
    """List the numbers read off the marker pegs."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    seen, say = [], []
    for v in lst(peg_numbers):
        d = ''.join(c for c in str(v) if c.isdigit())
        if d:
            seen.append(d)
            say.append('a peg lettered %s' % d)
    return {'seen': seen, 'n': len(seen),
            'verdict': '; '.join(say) or 'no numbered peg was read'}

# end of code_pegs
