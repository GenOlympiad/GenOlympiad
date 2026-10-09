# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_drift_side
def worst_drift_angle(key_reads, hour_reads, old_groyne_read, keys):
    """Worst angle between each groyne's sand build up and the old groyne's direction."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def pick(v, opts):
        if v is None:
            return None
        s = ' '.join(str(v).lower().replace('-', ' ').split())
        if s in ('', 'none', 'n a', 'na', 'nil', 'empty', '?', '.'):
            return None
        for o in opts:
            if o in s:
                return o
        return None
    def hour(v):
        d = ''.join(c for c in str(v) if c.isdigit())
        x = int(d) if d and len(d) <= 2 else None
        return x if x is not None and 1 <= x <= 12 else None
    def deg(x):
        return ((x % 12) * 30.0 + 180.0) % 360.0 - 180.0
    def one(n):
        v = lst(n)
        return v[0] if v else None
    want = [str(x) for x in lst(keys)]
    r = hour(one(old_groyne_read))
    if r is None:
        return {'obs': 180.0, 'exp': 0.0, 'verdict': 'the old groyne was not read'}
    base = deg(r)
    got = align_by_printed_key([{'key': x, 'h': v} for x, v in zip(lst(key_reads), lst(hour_reads))], want)
    worst, say, seen = 0.0, [], 0
    for i, row in enumerate(got):
        rr = row if isinstance(row, dict) else {}
        x = hour(rr.get('h'))
        if x is None:
            return {'obs': 180.0, 'exp': 0.0,
                    'verdict': 'groyne %s not read' % (want[i] if i < len(want) else i)}
        seen += 1
        d = abs((deg(x) - base + 180.0) % 360.0 - 180.0)
        worst = d if d > worst else worst
        say.append('groyne %s builds toward %d oclock against the old groyne at %d'
                   % (want[i], x, r))
    if seen < len(want):
        return {'obs': 180.0, 'exp': 0.0, 'verdict': 'only %d of %d groynes read' % (seen, len(want))}
    return {'obs': worst, 'exp': 0.0, 'verdict': '; '.join(say) + ' | worst %g' % worst}

# end of code_drift_side

# shared code: code_keyed_yes_count
def keyed_yes(key_reads, question_reads, keys):
    """Count the groynes answered yes, matched by their printed number."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    want = [str(x) for x in lst(keys)]
    got = align_by_printed_key([{'key': x, 'q': v} for x, v in zip(lst(key_reads), lst(question_reads))], want)
    n, say = 0, []
    for i, row in enumerate(got):
        r = row if isinstance(row, dict) else {}
        yes = str(r.get('q')).strip().lower().startswith('y')
        if yes:
            n += 1
        say.append('%s: %s' % (want[i] if i < len(want) else i, 'yes' if yes else 'no'))
    return {'n': n, 'asked': len(want), 'verdict': '; '.join(say) or 'nothing was read'}

# end of code_keyed_yes_count
