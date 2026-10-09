# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_lot_grouping
def check_lot_grouping(names, shades, pairs, pale_quota):
    """Count matched seam pairs cut from one roll, zero if the pale roll piece count is wrong."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def key(v):
        s = ''.join(c if c.isalpha() else ' ' for c in str(v).upper())
        return ' '.join(s.split())
    def side(v):
        w = str(v).lower()
        return 'pale' if 'pale' in w else ('deep' if 'deep' in w else None)
    where = {}
    for k, s in zip(lst(names), lst(shades)):
        t = side(s)
        if key(k) and t:
            where[key(k)] = t
    try:
        quota = int(pale_quota)
    except (TypeError, ValueError):
        quota = -1
    pale = 0
    for v in where.values():
        pale += 1 if v == 'pale' else 0
    ok, notes = 0, []
    for p in lst(pairs):
        bits = [key(b) for b in str(p).split('|')]
        a = where.get(bits[0]) if len(bits) > 1 else None
        b = where.get(bits[1]) if len(bits) > 1 else None
        ok += 1 if (a is not None and a == b) else 0
        notes.append('%s: %s and %s' % (str(p), a or 'not read', b or 'not read'))
    if pale != quota:
        ok = 0
    return {'ok': ok, 'n': len(where),
            'verdict': '; '.join(notes) + ' | %d pieces on the paler roll against a yield of %d'
                       % (pale, quota)}

# end of code_lot_grouping

# shared code: code_channel_clear
def channel_clear(answers, total):
    """Check every piece is read and none reaches across the bare channel."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def cls(v):
        w = str(v).lower()
        return 'wholly' if 'wholly' in w else ('across' if 'across' in w else None)
    got = []
    for x in lst(answers):
        c = cls(x)
        if c:
            got.append(c)
    try:
        n = int(total)
    except (TypeError, ValueError):
        n = -1
    bad = got.count('across')
    good = n > 0 and len(got) >= n and bad == 0
    return {'state': 'match' if good else 'mismatch', 'n': len(got),
            'verdict': '%d of %d pieces read, %d of them reach across the bare channel'
                       % (len(got), n, bad)}

# end of code_channel_clear
