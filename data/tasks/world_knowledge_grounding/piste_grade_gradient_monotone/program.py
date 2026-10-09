# shared code: code_mark_ranks
def mark_ranks_vs_gradients(mark_names, shapes, colours, profile_names, top_heights, bottom_heights, run_lengths, runs):
    """Each run's trail mark rank set against the rank its profile gradient gives."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def norm(v):
        return ' '.join(str(v).strip().lower().split())
    def num(v):
        s = ''.join(c for c in str(v) if c.isdigit() or c == '.')
        try:
            return float(s)
        except (TypeError, ValueError):
            return None
    def word(v, pool):
        w = norm(v)
        for k in pool:
            if k in w:
                return k
        return None
    rank_table = {('circle', 'green'): 1, ('square', 'blue'): 2, ('diamond', 'black'): 3,
           ('circle', 'blue'): 1, ('circle', 'red'): 2, ('circle', 'black'): 3}
    want = [norm(r) for r in lst(runs)]
    mark_rows = align_by_printed_key([{'key': norm(k), 's': s, 'c': c}
                               for k, s, c in zip(lst(mark_names), lst(shapes), lst(colours))], want)
    profile_rows = align_by_printed_key([{'key': norm(k), 't': t, 'b': b, 'l': l}
                               for k, t, b, l in zip(lst(profile_names), lst(top_heights), lst(bottom_heights), lst(run_lengths))], want)
    obs, grad, notes = [], [], []
    for i, k in enumerate(want):
        r = mark_rows[i] if i < len(mark_rows) else None
        p = profile_rows[i] if i < len(profile_rows) else None
        s = word(r.get('s'), ('circle', 'square', 'diamond')) if isinstance(r, dict) else None
        c = word(r.get('c'), ('green', 'blue', 'black', 'red')) if isinstance(r, dict) else None
        t = num(p.get('t')) if isinstance(p, dict) else None
        b = num(p.get('b')) if isinstance(p, dict) else None
        l = num(p.get('l')) if isinstance(p, dict) else None
        rank = rank_table.get((s, c))
        if rank is None or t is None or b is None or l is None or l <= 0:
            notes.append('%s: mark or profile not read' % k)
            continue
        obs.append('%s-%d' % (k, rank))
        grad.append((k, (t - b) / l))
        notes.append('%s: mark ranks %d, profile falls %g over %g' % (k, rank, t - b, l))
    if not want or len(obs) != len(want):
        return {'obs': [], 'exp': ['not read'], 'n': len(obs),
                'verdict': '; '.join(notes) + ' | not every run was read on both panels'}
    order = sorted(grad, key=lambda g: g[1])
    exp = ['%s-%d' % (order[j][0], j + 1) for j in range(len(order))]
    return {'obs': obs, 'exp': exp, 'n': len(obs),
            'verdict': '; '.join(notes) + ' | the profiles rank them ' + ' '.join(exp)}

# end of code_mark_ranks

# shared code: code_profile_slopes
def profile_gradients(profile_names, top_heights, bottom_heights, run_lengths, runs):
    """The percent gradient of each run's profile chart, in run order."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def norm(v):
        return ' '.join(str(v).strip().lower().split())
    def num(v):
        s = ''.join(c for c in str(v) if c.isdigit() or c == '.')
        try:
            return float(s)
        except (TypeError, ValueError):
            return None
    want = [norm(r) for r in lst(runs)]
    got = align_by_printed_key([{'key': norm(k), 't': t, 'b': b, 'l': l}
                                for k, t, b, l in zip(lst(profile_names), lst(top_heights), lst(bottom_heights), lst(run_lengths))], want)
    seq, notes = [], []
    for i, k in enumerate(want):
        p = got[i] if i < len(got) else None
        t = num(p.get('t')) if isinstance(p, dict) else None
        b = num(p.get('b')) if isinstance(p, dict) else None
        l = num(p.get('l')) if isinstance(p, dict) else None
        if t is None or b is None or l is None or l <= 0:
            notes.append('%s: profile not read' % k)
            continue
        seq.append(round(100.0 * (t - b) / l, 3))
        notes.append('%s: falls %g over %g, that is %g per cent'
                   % (k, t - b, l, round(100.0 * (t - b) / l, 3)))
    return {'seq': seq, 'n': len(seq),
            'verdict': '; '.join(notes) or 'no profile chart was read'}

# end of code_profile_slopes

# shared code: code_mark_family
def marks_match_house_set(shapes, colours, runs):
    """Whether the trail marks read are exactly a green circle, blue square and black diamond."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def norm(v):
        return ' '.join(str(v).strip().lower().split())
    def word(v, pool):
        w = norm(v)
        for k in pool:
            if k in w:
                return k
        return None
    house = set([('circle', 'green'), ('square', 'blue'), ('diamond', 'black')])
    n_want = len(lst(runs))
    seen, notes = [], []
    for s, c in zip(lst(shapes), lst(colours)):
        sw = word(s, ('circle', 'square', 'diamond'))
        cw = word(c, ('green', 'blue', 'black', 'red'))
        if sw is None or cw is None:
            notes.append('a mark was not read')
            continue
        seen.append((sw, cw))
        notes.append('mark read as %s %s' % (cw, sw))
    good = n_want > 0 and len(seen) == n_want and set(seen) == house
    return {'state': 'match' if good else 'mismatch', 'n': len(seen),
            'verdict': '; '.join(notes) or 'no mark was read'}

# end of code_mark_family
