# code: helpers
from genolympiad.task_helpers import sweep_holds_nothing_banned
# end of helpers

# shared code: code_read
def _t(v):
    return ' '.join(str('' if v is None else v).split()).strip(' .,:;-').lower()


def _head(v):
    return _t(v).lstrip('*_"\'([ ')


def _yn(node, i=0):
    a = (node or {}).get('answers') or []
    h = _head(a[i]) if i < len(a) else ''
    if h.startswith('yes'):
        return 'y'
    if h.startswith('no') or h.startswith('none'):
        return 'n'
    return '?'


def read_key_texts(keys, vals):
    ks = [_t(k) for k in (keys or {}).get('answers') or []]
    vs = [_t(v) for v in (vals or {}).get('answers') or []]
    rows = {}
    for i, k in enumerate(ks):
        if not k or k == 'none' or k in rows:
            continue
        rows[k] = (vs[i] if i < len(vs) and vs[i] else 'nothing')
    if not rows:
        return {'seq': 'none', 'refused': True,
                'verdict': 'no printed key came back from any cut-out, so no reading can be '
                           'attached to anything -> abstain rather than zero the card'}
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'n': len(rows), 'verdict': 'the page reads back as %s' % seq}


def read_key_values(keys, vals):
    ks = [_t(k) for k in (keys or {}).get('answers') or []]
    vs = []
    for v in (vals or {}).get('answers') or []:
        keep = ''.join(c for c in _t(v) if c.isdigit() or c in '.:').strip('.:')
        vs.append(keep)
    rows = {}
    for i, k in enumerate(ks):
        if not k or k == 'none' or k in rows:
            continue
        rows[k] = (vs[i] if i < len(vs) and vs[i] else 'nothing')
    if not rows:
        return {'seq': 'none', 'refused': True,
                'verdict': 'no printed key came back from any cut-out -> abstain rather than '
                           'zero the card'}
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'n': len(rows), 'verdict': 'the page reads back as %s' % seq}


def amap(keys, vals):
    ks = [_t(k) for k in (keys or {}).get('answers') or []]
    vs = [''.join(c for c in _t(v) if c.isalpha()) for v in (vals or {}).get('answers') or []]
    rows = {}
    for i, k in enumerate(ks):
        if not k or k == 'none' or k in rows:
            continue
        rows[k] = (vs[i] if i < len(vs) and vs[i] else 'nothing')
    if not rows:
        return {'seq': 'none', 'refused': True,
                'verdict': 'no printed key came back from any cut-out -> abstain rather than '
                           'zero the card'}
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'n': len(rows), 'verdict': 'the page reads back as %s' % seq}


def onefield(node):
    """The first non-empty value read for a field, or a refusal if it came back empty."""
    answers = (node or {}).get('answers') or []
    for raw in answers:
        t = _t(raw)
        if t and t != 'none':
            return {'val': t, 'verdict': 'the page reads %s there' % t}
    if [a for a in answers if str(a or '').strip()] and not (node or {}).get('unreadable'):
        return {'val': 'none',
                'verdict': 'the reader used the none this question designates for an empty field '
                           '-- that is a reading of an absence, not a refusal'}
    return {'val': 'none', 'refused': True,
            'verdict': 'that cut-out came back empty -> abstain rather than zero the card'}


def numfield(node):
    r = onefield(node)
    if r.get('refused'):
        return {'val': None, 'refused': True, 'verdict': r['verdict']}
    keep = ''.join(c for c in str(r['val']) if c.isdigit() or c in '.-')
    try:
        return {'val': float(keep), 'verdict': 'the page reads %s there' % keep}
    except Exception:
        return {'val': None, 'refused': True,
                'verdict': 'what came back (%s) is not a figure -> abstain' % r['val']}


def bothyes(a, b):
    x, y = _yn(a), _yn(b)
    if x == '?' or y == '?':
        return {'state': 'none', 'refused': True,
                'verdict': 'one of the two cut-out answers came back unusable -> abstain'}
    return {'state': ('yes' if x == 'y' and y == 'y' else 'no'),
            'verdict': 'first question %s, second question %s' % (x, y)}


def yesnot(a, b):
    x, y = _yn(a), _yn(b)
    if x == '?' or y == '?':
        return {'state': 'none', 'refused': True,
                'verdict': 'one of the two cut-out answers came back unusable -> abstain'}
    return {'state': ('yes' if x == 'y' and y == 'n' else 'no'),
            'verdict': 'first question %s, second question %s' % (x, y)}


def yn1(node):
    v = _yn(node)
    if v == '?':
        return {'state': 'none', 'refused': True,
                'verdict': 'that cut-out answer came back unusable -> abstain rather than zero'}
    return {'state': ('yes' if v == 'y' else 'no'), 'verdict': 'the reader answers %s' % v}


def first_word(node):
    r = onefield(node)
    w = [x for x in str(r.get('val') or '').split() if x]
    if r.get('refused') or not w or w[0] == 'none':
        return {'val': 'none', 'refused': True,
                'verdict': 'no usable word came back from that cut-out -> abstain rather than '
                           'zero the card'}
    return {'val': w[0], 'verdict': 'the reader answers %s' % w[0]}


def seqof(node):
    vs = [_t(v) for v in (node or {}).get('answers') or []]
    vs = [v for v in vs if v and v != 'none']
    if not vs:
        return {'seq': 'none', 'refused': True,
                'verdict': 'nothing came back from the cut-outs -> abstain'}
    return {'seq': '|'.join(vs), 'n': len(vs), 'verdict': 'the cut-outs read %s' % '|'.join(vs)}


def setof(node):
    r = onefield(node)
    if r.get('refused'):
        return {'seq': 'none', 'refused': True, 'verdict': r['verdict']}
    parts = [p for p in str(r['val']).replace(',', ' ').replace(';', ' ').split()
             if p and p not in ('and', '&')]
    if not parts or parts == ['none']:
        return {'seq': 'none', 'verdict': 'the field is empty and the reader said so'}
    return {'seq': '|'.join(sorted(set(parts))), 'verdict': 'the field lists %s' % ' '.join(sorted(set(parts)))}


def counted(node):
    ans = (node or {}).get('answers') or []
    if not ans:
        return {'n': -1, 'refused': True, 'verdict': 'no cut-out answered -> abstain'}
    n = sum(1 for a in ans if _head(a).startswith('yes'))
    return {'n': n, 'asked': len(ans),
            'verdict': '%d of the %d cut-outs confirmed their unit -> counted %d' % (n, len(ans), n)}


def _num(v):
    raw = str('' if v is None else v).strip().lstrip('([" \'')
    t = _t(v)
    neg = raw.startswith('-') or raw.startswith('\u2212') or t.startswith('minus')
    keep = ''.join(c for c in t if c.isdigit() or c == '.').strip('.')
    if not keep:
        return None
    try:
        f = float(keep)
    except Exception:
        return None
    return -f if neg else f


def _digitgroups(v):
    out, cur = [], ''
    for ch in _t(v):
        if ch.isdigit():
            cur += ch
        else:
            if cur:
                out.append(cur)
            cur = ''
    if cur:
        out.append(cur)
    return out


def _rows(keys, vals, numeric=False):
    ks = [_t(k) for k in (keys or {}).get('answers') or []]
    vs = (vals or {}).get('answers') or []
    out = []
    for i, k in enumerate(ks):
        if not k or k == 'none':
            continue
        raw = vs[i] if i < len(vs) else None
        out.append((k, _num(raw) if numeric else _t(raw)))
    return out


def sorted_distinct_reads(node):
    vs = [_t(v) for v in (node or {}).get('answers') or []]
    vs = [v.replace(' ', '') for v in vs if v and v != 'none']
    if not vs:
        return {'seq': 'none', 'refused': True,
                'verdict': 'nothing came back from the cut-outs -> abstain rather than zero'}
    u = sorted(set(vs))
    return {'seq': ','.join(u), 'n': len(u), 'verdict': 'the cut-outs read %s' % ','.join(u)}


def distinct(keys):
    ks = [_t(k) for k in (keys or {}).get('answers') or []]
    ks = [k for k in ks if k and k != 'none']
    if not ks:
        return {'n': -1, 'refused': True,
                'verdict': 'no printed key came back -> abstain rather than zero the card'}
    u = sorted(set(ks))
    return {'n': len(u), 'keys': ','.join(u),
            'verdict': '%d different keys came back: %s' % (len(u), ','.join(u))}


def tally(keys, vals, rkeys, rvals, wmap):
    units = _rows(keys, vals)
    rows = _rows(rkeys, rvals, numeric=True)
    if not units or not rows:
        return {'state': 'none', 'refused': True,
                'verdict': 'one of the two sides came back empty -> abstain rather than zero'}
    want = {}
    for k, grp in units:
        w = (wmap or {}).get(k)
        if w is None:
            return {'state': 'none', 'refused': True,
                    'verdict': 'a unit key came back that the job does not list (%s) -> abstain' % k}
        if not grp or grp == 'nothing' or grp == 'none':
            return {'state': 'none', 'refused': True,
                    'verdict': 'unit %s came back without a group number -> abstain' % k}
        want[grp] = want.get(grp, 0.0) + float(w)
    bad = []
    for grp, got in rows:
        if got is None:
            return {'state': 'none', 'refused': True,
                    'verdict': 'row %s came back without a figure -> abstain' % grp}
        if grp not in want:
            bad.append('row %s has no units wearing its number' % grp)
        elif abs(got - want[grp]) > 0.5:
            bad.append('row %s reads %s, its own units come to %s' % (grp, got, want[grp]))
    for grp in sorted(set(want) - set(g for g, _ in rows)):
        bad.append('the units wearing %s have no row at all' % grp)
    return {'state': ('no' if bad else 'yes'), 'n': len(rows),
            'verdict': ('; '.join(bad) if bad else
                        'every row equals the sum of the units wearing its own key')}


def under(vals, limit):
    xs = [_num(v) for v in (vals or {}).get('answers') or []]
    xs = [x for x in xs if x is not None]
    if not xs:
        return {'state': 'none', 'refused': True,
                'verdict': 'no figure came back -> abstain rather than zero the card'}
    over = [x for x in xs if x > float(limit) + 0.5]
    return {'state': ('no' if over else 'yes'), 'n': len(xs), 'worst': max(xs),
            'verdict': ('%s of %s pass the bound %s (worst %s)'
                        % (len(over), len(xs), limit, max(xs)) if over else
                        'the worst figure is %s against a bound of %s' % (max(xs), limit))}


def nzcount(keys, vals):
    rows = _rows(keys, vals, numeric=True)
    if not rows:
        return {'n': -1, 'refused': True,
                'verdict': 'no printed key came back -> abstain rather than zero the card'}
    seen, n = {}, 0
    for k, v in rows:
        if k in seen:
            continue
        seen[k] = v
        if v is not None and v > 0:
            n += 1
    return {'n': n, 'asked': len(seen),
            'verdict': '%d of the %d keyed places came back holding something' % (n, len(seen))}


def alldiff(keys, vals):
    rows = _rows(keys, vals)
    seen = {}
    for k, v in rows:
        if k not in seen:
            seen[k] = v
    vs = [v for v in seen.values() if v and v != 'none']
    if len(vs) < 2:
        return {'state': 'none', 'refused': True,
                'verdict': 'fewer than two readings came back -> abstain rather than zero'}
    return {'state': ('yes' if len(set(vs)) == len(vs) else 'no'), 'n': len(vs),
            'verdict': 'the readings are %s' % ', '.join('%s=%s' % (k, seen[k])
                                                         for k in sorted(seen))}


def notallsame(keys, vals):
    r = alldiff(keys, vals)
    if r.get('refused'):
        return r
    rows = _rows(keys, vals)
    seen = {}
    for k, v in rows:
        if k not in seen:
            seen[k] = v
    vs = [v for v in seen.values() if v and v != 'none']
    return {'state': ('no' if len(set(vs)) == 1 else 'yes'), 'n': len(vs),
            'verdict': r['verdict']}


def samevals(keys, vals):
    rows = _rows(keys, vals)
    seen = {}
    for k, v in rows:
        if k not in seen:
            seen[k] = v
    vs = [v for v in seen.values() if v and v != 'none' and v != 'nothing']
    if len(vs) < 2:
        return {'state': 'none', 'refused': True,
                'verdict': 'fewer than two carriers came back -> abstain rather than zero'}
    return {'state': ('yes' if len(set(vs)) == 1 else 'no'), 'n': len(vs),
            'verdict': 'the carriers read %s' % ', '.join('%s=%s' % (k, seen[k])
                                                          for k in sorted(seen))}


def marked(keys, flags):
    ks = [_t(k) for k in (keys or {}).get('answers') or []]
    fs = (flags or {}).get('answers') or []
    rows = [(k, _head(fs[i]) if i < len(fs) else '')
            for i, k in enumerate(ks) if k and k != 'none']
    if not rows:
        return {'val': 'none', 'refused': True,
                'verdict': 'no keyed item came back at all -> abstain rather than zero the card'}
    hits = []
    for k, h in rows:
        if h.startswith('yes'):
            hits.append(k)
        elif not (h.startswith('no') or h.startswith('none')):
            return {'val': 'none', 'refused': True,
                    'verdict': 'the mark question came back unusable on %s -> abstain' % k}
    if len(hits) != 1:
        return {'val': ('none' if not hits else ','.join(sorted(hits))),
                'n': len(hits),
                'verdict': '%d items carry the mark, so no single one is named' % len(hits)}
    return {'val': hits[0], 'n': 1, 'verdict': 'the mark is on %s' % hits[0]}


def equalpair(keys, vals):
    rows = _rows(keys, vals, numeric=True)
    seen = {}
    for k, v in rows:
        if k not in seen:
            seen[k] = v
    if len([v for v in seen.values() if v is not None]) < 2:
        return {'seq': 'none', 'refused': True,
                'verdict': 'fewer than two figures came back -> abstain rather than zero'}
    ks = sorted(k for k in seen if seen[k] is not None)
    pair = []
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            if abs(seen[ks[i]] - seen[ks[j]]) < 1e-6:
                pair.append(ks[i] + '|' + ks[j])
    return {'seq': (pair[0] if len(pair) == 1 else ('none' if not pair else 'several')),
            'verdict': 'the figures are %s' % ', '.join('%s=%s' % (k, seen[k]) for k in ks)}


def settling(keys, vals):
    rows = _rows(keys, vals, numeric=True)
    seen = {}
    for k, v in rows:
        if k not in seen:
            seen[k] = v
    ks = sorted(seen)
    xs = [seen[k] for k in ks if seen[k] is not None]
    if len(xs) < 2 or len(xs) != len(ks):
        return {'state': 'none', 'refused': True,
                'verdict': 'the corrections did not all come back as figures -> abstain'}
    same = all((x > 0) == (xs[0] > 0) and x != 0 for x in xs)
    smaller = all(abs(xs[i + 1]) < abs(xs[i]) for i in range(len(xs) - 1))
    return {'state': ('yes' if same else 'no'), 'n': len(xs),
            'verdict': 'the corrections read %s (same way: %s, getting smaller: %s)'
                       % (', '.join(str(x) for x in xs), same, smaller)}


def sums(keys, vals, tot):
    rows = _rows(keys, vals, numeric=True)
    seen = {}
    for k, v in rows:
        if k not in seen:
            seen[k] = v
    xs = [v for v in seen.values() if v is not None]
    ta = (tot or {}).get('answers') or [] if isinstance(tot, dict) else [tot]
    t = _num(ta[0]) if ta else None
    if not xs or t is None:
        return {'state': 'none', 'refused': True,
                'verdict': 'either the entries or the total came back unusable -> abstain'}
    s = sum(xs)
    return {'state': ('yes' if abs(s - t) < 1e-6 else 'no'), 'total': t, 'sum': s,
            'verdict': 'the entries come to %s and the total box reads %s' % (s, t)}


def markrule(keys, marks, counts):
    a = _rows(keys, marks)
    b = _rows(keys, counts, numeric=True)
    ma, mb = {}, {}
    for k, v in a:
        ma.setdefault(k, v)
    for k, v in b:
        mb.setdefault(k, v)
    ks = [k for k in sorted(ma) if k in mb]
    if not ks:
        return {'state': 'none', 'refused': True,
                'verdict': 'no line came back with both readings -> abstain rather than zero'}
    bad = []
    for k in ks:
        m, c = ma[k], mb[k]
        if not m or m == 'none' or c is None:
            return {'state': 'none', 'refused': True,
                    'verdict': 'line %s came back unusable -> abstain' % k}
        doubled = m.startswith('two')
        if doubled != (c > 1):
            bad.append('line %s carries %s mark(s) for %s number(s)' % (k, m, c))
    return {'state': ('no' if bad else 'yes'), 'n': len(ks),
            'verdict': ('; '.join(bad) if bad else
                        'every line doubles its mark exactly where it cites more than one')}


def wordset(node):
    r = onefield(node)
    if r.get('refused'):
        return {'seq': 'none', 'refused': True, 'verdict': r['verdict']}
    parts = [p for p in str(r['val']).replace(',', ' ').replace(';', ' ').split()
             if p and p not in ('and', '&')]
    if not parts or parts == ['none']:
        return {'seq': 'none', 'verdict': 'nothing was named there and the reader said so'}
    u = sorted(set(parts))
    return {'seq': ','.join(u), 'n': len(u), 'verdict': 'the cut-out names %s' % ','.join(u)}


def first_word(node):
    r = onefield(node)
    if r.get('refused'):
        return {'val': 'none', 'refused': True, 'verdict': r['verdict']}
    w = [x for x in str(r.get('val') or '').split() if x]
    if not w:
        return {'val': 'none', 'refused': True,
                'verdict': 'that cut-out came back empty -> abstain rather than zero the card'}
    return {'val': w[0], 'verdict': 'the reader answers %s' % w[0]}


def numfield(node):
    r = onefield(node)
    if r.get('refused'):
        return {'val': None, 'refused': True, 'verdict': r['verdict']}
    if _t(r['val']) == 'none':
        return {'val': None,
                'verdict': 'the reader used the none this question designates for an empty box '
                           '-- that is a reading of an absence, not a refusal'}
    v = _num(r['val'])
    if v is None:
        return {'val': None, 'refused': True,
                'verdict': 'what came back (%s) is not a figure -> abstain' % r['val']}
    return {'val': v, 'verdict': 'the page reads %s there' % v}


def picks(*nodes):
    """Join the first word read from each field, refusing if any field is unusable."""
    vals = []
    for node in nodes:
        r = first_word(node)
        if r.get('refused'):
            return {'seq': 'none', 'refused': True, 'verdict': r['verdict']}
        vals.append(r['val'])
    if not vals:
        return {'seq': 'none', 'refused': True,
                'verdict': 'no read came back -> abstain rather than zero the card'}
    return {'seq': '|'.join(vals), 'n': len(vals),
            'verdict': 'the reads give %s' % '|'.join(vals)}


def hdrpick(node, want):
    rows = []
    for raw in (node or {}).get('answers') or []:
        if not _t(raw):
            return {'seq': 'none', 'refused': True,
                    'verdict': 'a header line came back empty -> abstain rather than zero'}
        nums = _digitgroups(raw)
        if len(nums) < 4:
            rows.append('short')
            continue
        rows.append('.'.join(nums[int(i)] for i in str(want)))
    if not rows:
        return {'seq': 'none', 'refused': True,
                'verdict': 'no header line came back -> abstain rather than zero the card'}
    return {'seq': '|'.join(rows), 'n': len(rows),
            'verdict': 'the header lines give %s' % '|'.join(rows)}


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

# shared code: code_flow_b
def _w_t(v):
    return ' '.join(str('' if v is None else v).split()).strip(' .,:;-').lower()


def _w_words(v):
    t = _w_t(v).replace(',', ' ').replace(';', ' ').replace('/', ' ')
    return [w for w in t.split() if w and w not in ('and', '&', 'the')]


def _w_num(v):
    t = _w_t(v)
    keep = ''.join(c for c in t if c.isdigit() or c == '.').strip('.')
    try:
        return float(keep)
    except Exception:
        return None


def pairset(node):
    out = []
    for raw in (node or {}).get('answers') or []:
        w = _w_words(raw)
        if not w or w[0] == 'none':
            continue
        if len(w) < 2:
            return {'seq': 'none', 'refused': True,
                    'verdict': 'a cut-out named only one marking (%s), so the pair it joins '
                               'cannot be made out -> abstain rather than zero the card' % raw}
        out.append('-'.join(sorted(w[:2])))
    if not out:
        return {'seq': 'none', 'refused': True,
                'verdict': 'no cut-out named a pair of markings -> abstain rather than zero'}
    u = sorted(set(out))
    return {'seq': ','.join(u), 'n': len(u), 'verdict': 'the links join %s' % ','.join(u)}


def stepchange(node):
    sets, seen = [], (node or {}).get('answers') or []
    for raw in seen:
        w = _w_words(raw)
        if not w or w == ['none']:
            return {'state': 'none', 'refused': True,
                    'verdict': 'one panel came back with no places at all -> abstain'}
        sets.append(frozenset(w))
    if len(sets) < 2:
        return {'state': 'none', 'refused': True,
                'verdict': 'fewer than two panels came back -> abstain rather than zero'}
    bad = []
    for i in range(len(sets) - 1):
        gone = sets[i] - sets[i + 1]
        came = sets[i + 1] - sets[i]
        if len(gone) != 1 or len(came) != 1:
            bad.append('step %d moves %d off and %d on' % (i + 1, len(gone), len(came)))
    return {'state': ('no' if bad else 'yes'), 'n': len(sets),
            'verdict': ('; '.join(bad) if bad else
                        'every step moves exactly one thing') +
                       ' -- panels read ' + ' | '.join(','.join(sorted(s)) for s in sets)}


def vacatedcovered(occ, cov):
    sets, covers = [], []
    for raw in (occ or {}).get('answers') or []:
        w = _w_words(raw)
        if not w or w == ['none']:
            return {'state': 'none', 'refused': True,
                    'verdict': 'a panel came back with no places -> abstain rather than zero'}
        sets.append(frozenset(w))
    for raw in (cov or {}).get('answers') or []:
        w = _w_words(raw)
        covers.append(w[0] if w else '')
    if len(sets) < 2 or len(covers) < len(sets) - 1:
        return {'state': 'none', 'refused': True,
                'verdict': 'the two reads did not cover the same panels -> abstain'}
    bad = []
    for i in range(len(sets) - 1):
        gone = sorted(sets[i] - sets[i + 1])
        if not covers[i]:
            return {'state': 'none', 'refused': True,
                    'verdict': 'panel %d did not say what was under cover -> abstain' % (i + 1)}
        if len(gone) != 1:
            bad.append('step %d does not empty exactly one place' % (i + 1))
        elif gone[0] != covers[i]:
            bad.append('step %d empties %s but %s was the covered place'
                       % (i + 1, gone[0], covers[i]))
    return {'state': ('no' if bad else 'yes'), 'n': len(sets),
            'verdict': ('; '.join(bad) if bad else
                        'each step empties the place that was under cover')}


def atleast(node, limit):
    ans = (node or {}).get('answers') or []
    xs = [_w_num(a) for a in ans]
    xs = [x for x in xs if x is not None]
    if not xs:
        return {'state': 'none', 'refused': True,
                'verdict': 'no figure came back -> abstain rather than zero the card'}
    worst = min(xs)
    return {'state': ('yes' if worst >= float(limit) - 1e-6 else 'no'), 'worst': worst,
            'verdict': 'the smallest figure read back is %s against a floor of %s'
                       % (worst, limit)}


def nicesteps(node):
    xs = []
    for raw in (node or {}).get('answers') or []:
        for w in _w_words(raw):
            v = _w_num(w)
            if v is not None:
                xs.append(v)
    xs = sorted(set(xs))
    if len(xs) < 3:
        return {'state': 'none', 'few': 'none', 'refused': True,
                'verdict': 'fewer than three axis figures came back -> abstain rather than zero'}
    gaps = [round(xs[i + 1] - xs[i], 6) for i in range(len(xs) - 1)]
    even = all(abs(g - gaps[0]) < 1e-6 for g in gaps) and gaps[0] > 0
    ladder = False
    if even:
        g = gaps[0]
        k = -6
        while k <= 9 and not ladder:
            for m in (1.0, 2.0, 5.0):
                if abs(g - m * (10.0 ** k)) < 1e-6 * max(1.0, g):
                    ladder = True
                    break
            k += 1
    return {'state': ('yes' if (even and ladder) else 'no'),
            'few': ('yes' if len(xs) <= 6 else 'no'),
            'n': len(xs), 'step': (gaps[0] if even else None),
            'verdict': 'the axis reads %s (even gaps: %s, on the one-two-five ladder: %s)'
                       % (', '.join(str(x) for x in xs), even, ladder)}

# end of code_flow_b
