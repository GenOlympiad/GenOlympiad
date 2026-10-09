# shared code: code_valves
def check_valve_chainages(chainages, valve_reads, shape_reads, plan):
    """Count chainages whose read valve type and ground shape differ from the survey plan."""
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
    def key(v):
        return ''.join(c for c in str(v) if c.isdigit())
    want = sorted(plan.keys(), key=lambda k: int(k))
    rows = [{'key': key(a), 'v': b, 's': c} for a, b, c in zip(lst(chainages), lst(valve_reads), lst(shape_reads))]
    got = align_by_printed_key(rows, want)
    miss, say = 0, []
    for i, k in enumerate(want):
        r = got[i] if i < len(got) else None
        v = word(r.get('v'), ('air', 'washout', 'none')) if isinstance(r, dict) else None
        s = word(r.get('s'), ('falls', 'rises', 'through')) if isinstance(r, dict) else None
        wv, ws = plan[k][0], plan[k][1]
        if v == wv and s == ws:
            say.append('chainage %s: %s valve on ground that %s' % (k, v, s))
        else:
            miss += 1
            say.append('chainage %s: read %s valve on ground that %s, the survey wants %s on '
                       'ground that %s' % (k, v, s, wv, ws))
    return {'miss': miss, 'n': len(want), 'verdict': '; '.join(say) or 'no chainage was read'}

# end of code_valves

# shared code: code_levels
def read_ground_levels(chainages, level_reads, order):
    """The ground levels read at each chainage, in the reference chainage order."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def num(v):
        s = ''.join(c for c in str(v) if c.isdigit() or c == '.')
        try:
            return float(s)
        except (TypeError, ValueError):
            return None
    def key(v):
        return ''.join(c for c in str(v) if c.isdigit())
    rows = [{'key': key(a), 'l': b} for a, b in zip(lst(chainages), lst(level_reads))]
    got = align_by_printed_key(rows, list(order))
    seq, say = [], []
    for i, k in enumerate(order):
        r = got[i] if i < len(got) else None
        l = num(r.get('l')) if isinstance(r, dict) else None
        if l is None:
            say.append('chainage %s: no ground level read' % k)
            continue
        seq.append(l)
        say.append('chainage %s: ground %g' % (k, l))
    return {'seq': seq, 'n': len(seq),
            'verdict': '; '.join(say) or 'no ground level was read'}

# end of code_levels
