# code: helpers
from genolympiad.task_helpers import sweep_holds_nothing_banned
# end of helpers

# shared code: code_flow_a
def _t(s):
    return ' '.join(str(s or '').lower().split()).strip(' .,:-')
def _key(s, allow):
    t = _t(s)
    for k in str(allow).split('|'):
        if k and k in t:
            return k
    return ''
def tmap(keys, vals, allow):
    ks = [_key(k, allow) for k in (keys or {}).get('answers') or []]
    vs = [_t(v) for v in (vals or {}).get('answers') or []]
    rows = {}
    for i, k in enumerate(ks):
        if not k or k in rows or i >= len(vs):
            continue
        rows[k] = ''.join(ch for ch in vs[i] if ch.isalnum() or ch == '.') or 'none'
    n = len([k for k in str(allow).split('|') if k])
    if len(rows) < n:
        return {'seq': 'none', 'refused': True,
                'verdict': 'only %d of %d rows came back keyed -> abstain' % (len(rows), n)}
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'verdict': 'read back as %s' % seq}
def map_bottle_to_reading(keys, vals, allow):
    """Key each label reading to its bottle, abstaining if any bottle is missing."""
    bottles = [_key(k, allow) for k in (keys or {}).get('answers') or []]
    readings = []
    for v in (vals or {}).get('answers') or []:
        t = ''.join(ch if ch.isalnum() else ' ' for ch in _t(v)).split()
        t = [w for w in t if w != 'none']
        readings.append(''.join(t))
    rows = {}
    for i, k in enumerate(bottles):
        if not k or k in rows or i >= len(readings):
            continue
        rows[k] = readings[i] or 'none'
    n = len([k for k in str(allow).split('|') if k])
    if len(rows) < n:
        return {'seq': 'none', 'refused': True,
                'verdict': 'only %d of %d labels came back keyed -> abstain' % (len(rows), n)}
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'verdict': 'the labels read %s' % seq}

# end of code_flow_a
