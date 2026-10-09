# code: helpers
from genolympiad.task_helpers import sweep_holds_nothing_banned
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
    vals = [a for a in _list(node) if a and a != 'none']
    if not vals:
        return {'val': 'none', 'refused': True,
                'verdict': 'the cut-out for the %s came back empty -> abstain' % name}
    top = max(set(vals), key=vals.count)
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
    for a in _list(node):
        f = _fig(a)
        if f:
            return {'val': f, 'verdict': 'the %s reads %s' % (name, f)}
    return {'val': 'none', 'refused': True,
            'verdict': 'no figure came back for the %s -> abstain' % name}


def pairs(keys, vals, name, least):
    """Pair each key with the first word of its value, withheld if too few keys came back."""
    keys_read, values_read = _list(keys), _list(vals)
    by_key = {}
    for i, k in enumerate(keys_read):
        if not k or k == 'none' or k in by_key:
            continue
        v = values_read[i] if i < len(values_read) else ''
        by_key[k] = v.split()[0] if v else 'nothing'
    if len(by_key) < least:
        return {'seq': 'none', 'refused': True,
                'verdict': 'only %d of the %s came back keyed, %d were wanted -> abstain'
                           % (len(by_key), name, least)}
    seq = '|'.join('%s=%s' % (k, by_key[k]) for k in sorted(by_key))
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
    """Whether every answer starts with the wanted word, given enough came back."""
    values = [a for a in _list(node) if a]
    if len(values) < least:
        return {'all': 'none', 'refused': True,
                'verdict': 'only %d of the %s came back readable, %d were wanted -> abstain'
                           % (len(values), name, least)}
    bad = [i + 1 for i, a in enumerate(values) if not a.startswith(want)]
    if bad:
        return {'all': 'no',
                'verdict': 'of the %d %s, number %s did not read %s'
                           % (len(values), name, ','.join(str(b) for b in bad), want)}
    return {'all': 'yes', 'verdict': 'all %d of the %s read %s' % (len(values), name, want)}


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


def figset(node, name, least):
    vals = [_fig(a) for a in _list(node)]
    vals = [v for v in vals if v]
    seen = []
    for v in vals:
        if v not in seen:
            seen.append(v)
    if len(seen) < least:
        return {'seq': 'none', 'refused': True,
                'verdict': 'only %d figure came back off the %s, %d were wanted -> abstain'
                           % (len(seen), name, least)}
    return {'seq': '|'.join(sorted(seen)),
            'verdict': 'the %s read back as %s' % (name, '|'.join(sorted(seen)))}


def falling(node, name, least):
    vals = [_fig(a) for a in _list(node)]
    vals = [v for v in vals if v]
    if len(vals) < least:
        return {'all': 'none', 'refused': True,
                'verdict': 'only %d figure came back off the %s, %d were wanted -> abstain'
                           % (len(vals), name, least)}
    nums = []
    for v in vals:
        try:
            nums.append(float(v))
        except Exception:
            return {'all': 'none', 'refused': True,
                    'verdict': 'a reading off the %s was not a figure -> abstain' % name}
    bad = [i + 2 for i in range(len(nums) - 1) if not nums[i] > nums[i + 1]]
    if bad:
        return {'all': 'no', 'verdict': 'reading down the %s, entry %s did not fall below the one '
                                        'above it (%s)' % (name, ','.join(str(b) for b in bad),
                                                           '>'.join(vals))}
    return {'all': 'yes', 'verdict': 'the %s falls all the way down (%s)' % (name, '>'.join(vals))}


def wordset(node, name, least):
    got = [a for a in _list(node) if a and a != 'none']
    seen = []
    for g in got:
        if g not in seen:
            seen.append(g)
    if len(seen) < least:
        return {'seq': 'none', 'refused': True,
                'verdict': 'only %d of the %s came back readable, %d were wanted -> abstain'
                           % (len(seen), name, least)}
    return {'seq': '|'.join(sorted(seen)),
            'verdict': 'the %s read back as %s' % (name, '|'.join(sorted(seen)))}


def _map(m):
    out = {}
    for part in str((m or {}).get('seq') or '').split('|'):
        if '=' in part:
            k, _, v = part.partition('=')
            out[k.strip()] = v.strip()
    return out


def ranking(m, order, name):
    rows, keys = _map(m), [k.strip() for k in order.split('>')]
    nums = []
    for k in keys:
        v = rows.get(k)
        try:
            nums.append(float(v))
        except Exception:
            return {'ok': 'none', 'refused': True,
                    'verdict': 'no figure came back for %s among the %s -> abstain' % (k, name)}
    bad = [keys[i + 1] for i in range(len(nums) - 1) if not nums[i] > nums[i + 1]]
    if bad:
        return {'ok': 'no', 'verdict': 'among the %s the wanted order is %s, and %s did not fall '
                                       'below what stands before it (%s)'
                                       % (name, order, ','.join(bad),
                                          '/'.join('%s=%g' % (k, n) for k, n in zip(keys, nums)))}
    return {'ok': 'yes', 'verdict': 'the %s stand in the order %s (%s)'
                                    % (name, order, '/'.join('%s=%g' % (k, n)
                                                             for k, n in zip(keys, nums)))}


def ratioband(m, top, bot, lo, hi, name):
    rows = _map(m)
    try:
        a, b = float(rows.get(top)), float(rows.get(bot))
    except Exception:
        return {'ok': 'none', 'refused': True,
                'verdict': 'both %s and %s have to come back as figures off the %s -> abstain'
                           % (top, bot, name)}
    if b == 0:
        return {'ok': 'none', 'refused': True,
                'verdict': 'the figure at %s came back as zero, so no ratio can be taken -> abstain'
                           % bot}
    r = a / b
    if lo <= r <= hi:
        return {'ok': 'yes', 'verdict': '%s over %s is %.2f, inside %.2f to %.2f'
                                        % (top, bot, r, lo, hi)}
    return {'ok': 'no', 'verdict': '%s over %s is %.2f, outside %.2f to %.2f'
                                   % (top, bot, r, lo, hi)}


def seen(present, node, absent='(blank)'):
    def _norm(v):
        return ' '.join(str('' if v is None else v).split()).strip(' .,:;-').lower()

    def _headword(v):
        return _norm(v).lstrip('*_"\'([ ')

    if (present or {}).get('unreadable') or (node or {}).get('unreadable'):
        return {'answers': [], 'unreadable': True}
    pa = (present or {}).get('answers') or []
    va = (node or {}).get('answers') or []
    if not pa or len(pa) != len(va):
        return {'answers': [], 'unreadable': True}
    out = []
    for i, praw in enumerate(pa):
        h = _headword(praw)
        v = _norm(va[i])
        got_text = bool(v) and v not in ('none', 'nothing')
        if h.startswith('yes'):
            if not got_text:
                return {'answers': [], 'unreadable': True}
            out.append(va[i])
        elif h.startswith('no'):
            out.append(va[i] if got_text else absent)
        else:
            return {'answers': [], 'unreadable': True}
    return {'answers': out}

# end of code_read
