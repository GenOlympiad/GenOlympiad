# code: helpers
from genolympiad.task_helpers import sweep_banned_unless_count_disagrees
# end of helpers

# shared code: code_read
def _t(v):
    return ' '.join(str('' if v is None else v).split()).strip()


def _clean(v):
    return _t(v).lower().strip(' .,:;-"\'')


def _list(node):
    return [_clean(a) for a in (node or {}).get('answers') or []]


def _fig(a):
    a = a.replace(',', '').replace(' ', '')
    got, seen = '', False
    for ch in a:
        if ch.isdigit():
            got += ch
            seen = True
        elif ch == '.' and seen and '.' not in got:
            got += '.'
        elif seen:
            break
    if '.' in got:
        got = got.rstrip('0').rstrip('.')
    return got


def most_common_read(node, name):
    """The most common non-empty answer read for the named field."""
    values = [a for a in _list(node) if a and a != 'none']
    if not values:
        return {'val': 'none', 'refused': True,
                'verdict': 'the cut-out for the %s came back empty -> abstain' % name}
    top = max(set(values), key=values.count)
    return {'val': top, 'verdict': 'the reader answers %s for the %s' % (top, name)}


def word(node, allowed, name):
    for a in _list(node):
        for w in allowed.split('|'):
            if a.startswith(w):
                return {'val': w, 'verdict': 'the %s reads %s' % (name, w)}
    return {'val': 'none', 'refused': True,
            'verdict': 'no word from the offered set came back for the %s -> abstain' % name}


def letter(node, allowed, name):
    ok = allowed.split('|')
    for a in _list(node):
        toks = [w for w in a.replace('.', ' ').replace(',', ' ').split() if w]
        cands = [w for w in toks if w in ok]
        if len(cands) == 1:
            return {'val': cands[0], 'verdict': 'the %s stands in band %s' % (name, cands[0])}
        t = ''.join(ch for ch in a if ch.isalnum())
        if t in ok:
            return {'val': t, 'verdict': 'the %s stands in band %s' % (name, t)}
    return {'val': 'none', 'refused': True,
            'verdict': 'no single band letter came back for the %s -> abstain' % name}


def first_figure_read(node, name):
    """The first figure found in the answers read for the named field."""
    for a in _list(node):
        f = _fig(a)
        if f:
            return {'val': f, 'verdict': 'the %s reads %s' % (name, f)}
    return {'val': 'none', 'refused': True,
            'verdict': 'no figure came back for the %s -> abstain' % name}


def pairs(keys, vals, name, least):
    ks, vs = _list(keys), _list(vals)
    rows = {}
    for i, k in enumerate(ks):
        if not k or k == 'none' or k in rows:
            continue
        v = vs[i] if i < len(vs) else ''
        rows[k] = v.split()[0] if v else 'nothing'
    if len(rows) < least:
        return {'seq': 'none', 'refused': True,
                'verdict': 'only %d of the %s came back keyed, %d were wanted -> abstain'
                           % (len(rows), name, least)}
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'verdict': 'the %s read back as %s' % (name, seq)}


def pairsfull(keys, vals, name, least):
    ks, vs = _list(keys), _list(vals)
    rows = {}
    for i, k in enumerate(ks):
        if not k or k == 'none' or k in rows:
            continue
        rows[k] = (vs[i] if i < len(vs) else '') or 'nothing'
    if len(rows) < least:
        return {'seq': 'none', 'refused': True,
                'verdict': 'only %d of the %s came back keyed, %d were wanted -> abstain'
                           % (len(rows), name, least)}
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'verdict': 'the %s read back as %s' % (name, seq)}


def figpairs(keys, vals, name, least):
    ks, vs = _list(keys), _list(vals)
    rows = {}
    for i, k in enumerate(ks):
        if not k or k == 'none' or k in rows:
            continue
        rows[k] = _fig(vs[i]) if i < len(vs) else ''
        if not rows[k]:
            rows[k] = 'nothing'
    if len(rows) < least:
        return {'seq': 'none', 'refused': True,
                'verdict': 'only %d of the %s came back keyed, %d were wanted -> abstain'
                           % (len(rows), name, least)}
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'verdict': 'the %s read back as %s' % (name, seq)}


def every(node, want, name, least):
    vals = [a for a in _list(node) if a]
    if len(vals) < least:
        return {'all': 'none', 'refused': True,
                'verdict': 'only %d of the %s came back readable, %d were wanted -> abstain'
                           % (len(vals), name, least)}
    bad = [i + 1 for i, a in enumerate(vals) if not a.startswith(want)]
    if bad:
        return {'all': 'no',
                'verdict': 'of the %d %s, number %s did not read %s'
                           % (len(vals), name, ','.join(str(b) for b in bad), want)}
    return {'all': 'yes', 'verdict': 'all %d of the %s read %s' % (len(vals), name, want)}


def caseone(node, name):
    got = [' '.join(str(a or '').split()) for a in (node or {}).get('answers') or []]
    got = [g for g in got if g and g.lower() != 'none']
    if not got:
        return {'val': 'none', 'refused': True,
                'verdict': 'the cut-out of the %s came back empty -> abstain' % name}
    top = max(set(got), key=got.count)
    return {'val': top, 'verdict': 'the %s reads %s' % (name, top)}


def caseset(node, name, least):
    got = [' '.join(str(a or '').split()) for a in (node or {}).get('answers') or []]
    got = [g for g in got if g and g.lower() != 'none']
    if len(got) < least:
        return {'seq': 'none', 'refused': True,
                'verdict': 'only %d of the %s came back readable, %d were wanted -> abstain'
                           % (len(got), name, least)}
    return {'seq': '|'.join(sorted(set(got))),
            'verdict': 'the %s read back as %s' % (name, '|'.join(sorted(set(got))))}


def figseq(node, name, least):
    vals = [_fig(a) for a in _list(node)]
    vals = [v for v in vals if v]
    if len(vals) < least:
        return {'seq': 'none', 'refused': True,
                'verdict': 'only %d figure came back off the %s, %d were wanted -> abstain'
                           % (len(vals), name, least)}
    return {'seq': '|'.join(vals), 'verdict': 'the %s read back as %s'
                                              % (name, '|'.join(vals))}

# end of code_read
