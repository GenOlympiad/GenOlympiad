# code: helpers
from genolympiad.task_helpers import count_listed_items, sweep_holds_nothing_banned
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
    ans = (node or {}).get('answers') or []
    for raw in ans:
        t = _t(raw)
        if t and t != 'none':
            return {'val': t, 'verdict': 'the page reads %s there' % t}
    if [a for a in ans if str(a or '').strip()] and not (node or {}).get('unreadable'):
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
    vals = []
    for nd in nodes:
        r = first_word(nd)
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

# end of code_read

# shared code: code_flow_c
def _q_t(v):
    return ' '.join(str('' if v is None else v).split()).strip(' .,:;-').lower()


def _q_head(v):
    return _q_t(v).lstrip('*_"\'([ ')


def _q_words(v):
    t = _q_t(v).replace(',', ' ').replace(';', ' ').replace('/', ' ')
    return [w for w in t.split() if w and w not in ('and', '&', 'the')]


def _q_num(v):
    raw = str('' if v is None else v).strip().lstrip('([" \'')
    t = _q_t(v)
    neg = raw.startswith('-') or raw.startswith(chr(0x2212)) or t.startswith('minus')
    keep = ''.join(c for c in t if c.isdigit() or c == '.').strip('.')
    if not keep:
        return None
    try:
        f = float(keep)
    except Exception:
        return None
    return -f if neg else f


def _q_yes(v):
    h = _q_head(v)
    if h.startswith('yes'):
        return 'y'
    if h.startswith('no') or h.startswith('none') or h.startswith('nothing'):
        return 'n'
    return '?'


def exactly_k_yes(node, k):
    """Whether exactly k of the close-up answers say yes, refusing if any is unusable."""
    answers = (node or {}).get('answers') or []
    if not answers:
        return {'state': 'none', 'refused': True,
                'verdict': 'no cut-out answered -> abstain rather than zero the card'}
    v = [_q_yes(a) for a in answers]
    if '?' in v:
        return {'state': 'none', 'refused': True,
                'verdict': 'a cut-out answer came back unusable -> abstain rather than zero'}
    n = v.count('y')
    return {'state': ('yes' if n == int(k) else 'no'), 'n': n, 'asked': len(v),
            'verdict': '%d of the %d cut-outs answered yes, against a required %s'
                       % (n, len(v), k)}


def whichyes(keys, flags):
    ks = [_q_t(k) for k in (keys or {}).get('answers') or []]
    fs = (flags or {}).get('answers') or []
    hit, seen = [], set()
    for i, k in enumerate(ks):
        if not k or k == 'none' or k in seen:
            continue
        seen.add(k)
        v = _q_yes(fs[i]) if i < len(fs) else '?'
        if v == '?':
            return {'seq': 'none', 'refused': True,
                    'verdict': 'the flag on %s came back unusable -> abstain rather than zero' % k}
        if v == 'y':
            hit.append(k)
    if not seen:
        return {'seq': 'none', 'refused': True,
                'verdict': 'no printed key came back -> abstain rather than zero the card'}
    u = sorted(set(hit))
    return {'seq': (','.join(u) if u else 'none'), 'n': len(u), 'asked': len(seen),
            'verdict': '%d of the %d keyed places answered yes: %s'
                       % (len(u), len(seen), ','.join(u) or 'none')}


def _q_series(node):
    xs = []
    for raw in (node or {}).get('answers') or []:
        xs.append(_q_num(raw))
    return xs


def monodir(node, want):
    xs = _q_series(node)
    if len(xs) < 2 or any(x is None for x in xs):
        return {'state': 'none', 'refused': True,
                'verdict': 'the figures did not all come back -> abstain rather than zero'}
    if str(want).startswith('up'):
        ok = all(xs[i + 1] > xs[i] for i in range(len(xs) - 1))
    else:
        ok = all(xs[i + 1] < xs[i] for i in range(len(xs) - 1))
    return {'state': ('yes' if ok else 'no'), 'n': len(xs),
            'verdict': 'the figures read %s against a required %s run'
                       % (', '.join(str(x) for x in xs), want)}


def slowing(node):
    xs = _q_series(node)
    if len(xs) < 3 or any(x is None for x in xs):
        return {'state': 'none', 'easing': 'none', 'refused': True,
                'verdict': 'the figures did not all come back -> abstain rather than zero'}
    d = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
    rise = all(x > 0 for x in d)
    ease = all(d[i + 1] < d[i] for i in range(len(d) - 1))
    return {'state': ('yes' if rise else 'no'), 'easing': ('yes' if ease else 'no'),
            'n': len(xs), 'steps': ','.join(str(x) for x in d),
            'verdict': 'the figures read %s, so the steps are %s'
                       % (', '.join(str(x) for x in xs), ', '.join(str(x) for x in d))}


def marked_group_order(marks, vals):
    """Whether the marked panels' values all exceed the rest and each group falls in order."""
    marks_read = [_q_yes(m) for m in (marks or {}).get('answers') or []]
    values = _q_series(vals)
    n = min(len(marks_read), len(values))
    if n < 3 or '?' in marks_read[:n] or any(x is None for x in values[:n]):
        return {'sep': 'none', 'mono': 'none', 'refused': True,
                'verdict': 'the panels did not all come back readable -> abstain rather than zero'}
    a = [values[i] for i in range(n) if marks_read[i] == 'y']
    b = [values[i] for i in range(n) if marks_read[i] == 'n']
    if not a or not b:
        return {'sep': 'no', 'mono': 'no', 'n': n,
                'verdict': 'one of the two groups is empty, so no ordering between them exists'}
    sep = min(a) > max(b)
    mono = (all(a[i + 1] < a[i] for i in range(len(a) - 1))
            and all(b[i + 1] < b[i] for i in range(len(b) - 1)))
    return {'sep': ('yes' if sep else 'no'), 'mono': ('yes' if mono else 'no'), 'n': n,
            'verdict': 'marked group reads %s and the rest reads %s'
                       % (', '.join(str(x) for x in a), ', '.join(str(x) for x in b))}


_OPP = {'left': 'right', 'right': 'left', 'up': 'down', 'down': 'up',
        'clockwise': 'anticlockwise', 'anticlockwise': 'clockwise',
        'forward': 'back', 'back': 'forward', 'towards': 'away', 'away': 'towards'}


def oppside(a, b):
    xa = _q_words(a.get('val') if isinstance(a, dict) and 'val' in a else a)
    xb = _q_words(b.get('val') if isinstance(b, dict) and 'val' in b else b)
    if isinstance(a, dict) and 'answers' in a:
        xa = _q_words((a.get('answers') or [''])[0])
    if isinstance(b, dict) and 'answers' in b:
        xb = _q_words((b.get('answers') or [''])[0])
    if not xa or not xb or xa[0] == 'none' or xb[0] == 'none':
        return {'state': 'none', 'refused': True,
                'verdict': 'one of the two direction reads came back empty -> abstain'}
    p, q = xa[0], xb[0]
    if p not in _OPP or q not in _OPP:
        return {'state': 'none', 'refused': True,
                'verdict': 'a direction word came back that is not in the closed set -> abstain'}
    return {'state': ('yes' if _OPP[p] == q else 'no'), 'pair': p + '|' + q,
            'verdict': 'the two reads are %s and %s' % (p, q)}


def _q_boxes(node):
    g = list((node or {}).get('geometry') or [])
    out = []
    for b in g:
        try:
            y0, x0, y1, x1 = [float(v) for v in list(b)[:4]]
            out.append(((y0 + y1) / 2.0, (x0 + x1) / 2.0))
        except Exception:
            out.append(None)
    return out


def deictic(pics, picids, caps, capids, capwords):
    pb, cb = _q_boxes(pics), _q_boxes(caps)
    pk = [_q_t(k) for k in (picids or {}).get('answers') or []]
    ck = [_q_t(k) for k in (capids or {}).get('answers') or []]
    cw = [_q_words(w) for w in (capwords or {}).get('answers') or []]
    P, C, W = {}, {}, {}
    for i, k in enumerate(pk):
        if k and k != 'none' and i < len(pb) and pb[i] and k not in P:
            P[k] = pb[i]
    for i, k in enumerate(ck):
        if k and k != 'none' and i < len(cb) and cb[i] and k not in C:
            C[k] = cb[i]
            W[k] = (cw[i][0] if i < len(cw) and cw[i] else '')
    keys = sorted(set(P) & set(C))
    if len(keys) < 2:
        return {'seq': 'none', 'refused': True,
                'verdict': 'fewer than two plates could be matched to a caption -> abstain'}
    out = []
    for k in keys:
        (py, px), (cy, cx) = P[k], C[k]
        if (px < 500.0) != (cx < 500.0):
            want = 'opposite'
        elif abs(py - cy) >= abs(px - cx):
            want = 'above' if py < cy else 'below'
        else:
            want = 'left' if px < cx else 'right'
        got = W.get(k) or 'nothing'
        out.append('%s=%s/%s' % (k, want, got))
        if got != want:
            return {'seq': 'no', 'detail': ' | '.join(out),
                    'verdict': 'plate %s sits %s of its caption but the caption says %s -- %s'
                               % (k, want, got, ' | '.join(out))}
    return {'seq': 'yes', 'n': len(keys), 'detail': ' | '.join(out),
            'verdict': 'every caption names where its own plate really sits -- %s'
                       % ' | '.join(out)}


def atleast(node, limit):
    xs = [x for x in _q_series(node) if x is not None]
    if not xs:
        return {'state': 'none', 'refused': True,
                'verdict': 'no figure came back -> abstain rather than zero the card'}
    worst = min(xs)
    return {'state': ('yes' if worst >= float(limit) - 1e-6 else 'no'), 'worst': worst,
            'verdict': 'the smallest figure read back is %s against a floor of %s'
                       % (worst, limit)}


def ratioband(node, want, tol):
    xs = [x for x in _q_series(node) if x is not None]
    if len(xs) < 2:
        return {'state': 'none', 'refused': True,
                'verdict': 'fewer than two figures came back -> abstain rather than zero'}
    if xs[1] == 0:
        return {'state': 'no', 'verdict': 'the second figure is zero, so no ratio exists'}
    r = xs[0] / xs[1]
    ok = abs(r - float(want)) <= float(tol)
    return {'state': ('yes' if ok else 'no'), 'ratio': round(r, 4),
            'verdict': 'the two figures read %s and %s, a ratio of %s against a wanted %s'
                       % (xs[0], xs[1], round(r, 4), want)}


def boxrel(a, b):
    pa, pb = _q_boxes(a), _q_boxes(b)
    pa = [p for p in pa if p]
    pb = [p for p in pb if p]
    if len(pa) != 1 or len(pb) != 1:
        return {'val': 'none', 'refused': True,
                'verdict': 'one of the two rings did not come back with exactly one rectangle '
                           '-> abstain rather than zero the card'}
    (ay, ax), (by, bx) = pa[0], pb[0]
    dy, dx = ay - by, ax - bx
    if abs(dy) >= abs(dx):
        v = 'below' if dy > 0 else 'above'
    else:
        v = 'right' if dx > 0 else 'left'
    return {'val': v, 'dy': round(dy, 1), 'dx': round(dx, 1),
            'verdict': 'the first rectangle sits %s the second, by %s down and %s across'
                       % (v, round(dy, 1), round(dx, 1))}


def keyedrun(keys, vals, order, want):
    ks = [_q_t(k) for k in (keys or {}).get('answers') or []]
    xs = _q_series(vals)
    m = {}
    for i, k in enumerate(ks):
        if k and k != 'none' and k not in m and i < len(xs):
            m[k] = xs[i]
    seq = [_q_t(o) for o in str(order).split(',') if _q_t(o)]
    run = [m.get(k) for k in seq]
    if any(v is None for v in run):
        return {'state': 'none', 'refused': True,
                'verdict': 'not every stated key came back with a figure -> abstain rather '
                           'than zero the card -- got %s' % m}
    if str(want).startswith('up'):
        ok = all(run[i + 1] > run[i] for i in range(len(run) - 1))
    else:
        ok = all(run[i + 1] < run[i] for i in range(len(run) - 1))
    return {'state': ('yes' if ok else 'no'), 'n': len(run),
            'verdict': 'in the stated key order the figures read %s against a required %s run'
                       % (', '.join(str(x) for x in run), want)}


def ratio2(a, b, want, tol):
    xa = _q_num(((a or {}).get('answers') or [None])[0])
    xb = _q_num(((b or {}).get('answers') or [None])[0])
    if xa is None or xb is None or xb == 0:
        return {'state': 'none', 'refused': True,
                'verdict': 'one of the two figures did not come back usable -> abstain'}
    r = xa / xb
    return {'state': ('yes' if abs(r - float(want)) <= float(tol) else 'no'),
            'ratio': round(r, 4),
            'verdict': 'the two figures read %s and %s, a ratio of %s against a wanted %s'
                       % (xa, xb, round(r, 4), want)}


def satpoint(keys, vals, mk):
    ks = [_q_t(k) for k in (keys or {}).get('answers') or []]
    xs = _q_series(vals)
    m = {}
    for i, k in enumerate(ks):
        v = _q_num(k)
        if v is not None and v not in m and i < len(xs) and xs[i] is not None:
            m[v] = xs[i]
    ts = sorted(m)
    if len(ts) < 3:
        return {'state': 'none', 'rising': 'none', 'easing': 'none', 'refused': True,
                'verdict': 'fewer than three timed readings came back -> abstain'}
    ys = [m[t] for t in ts]
    d = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
    rising = all(x > 0 for x in d)
    easing = all(d[i + 1] < d[i] for i in range(len(d) - 1))
    pick = None
    for t in ts:
        u = t * 2
        if u in m and m[t] > 0 and (m[u] - m[t]) / m[t] < 0.10:
            pick = t
            break
    got = _q_num(((mk or {}).get('answers') or [None])[0])
    if got is None:
        return {'state': 'none', 'rising': ('yes' if rising else 'no'),
                'easing': ('yes' if easing else 'no'), 'refused': True,
                'verdict': 'the marked point did not come back with a time -> abstain'}
    return {'state': ('yes' if (pick is not None and abs(got - pick) < 1e-6) else 'no'),
            'rising': ('yes' if rising else 'no'), 'easing': ('yes' if easing else 'no'),
            'picked': pick, 'marked': got,
            'verdict': 'the readings are %s, so the rule picks %s and the sheet marks %s'
                       % (', '.join('%s=%s' % (t, m[t]) for t in ts), pick, got)}

# end of code_flow_c
