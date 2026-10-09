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
    """Pair each printed key with the figure read beside it; refuse when no key is read."""
    key_reads = [_t(k) for k in (keys or {}).get('answers') or []]
    value_reads = []
    for v in (vals or {}).get('answers') or []:
        keep = ''.join(c for c in _t(v) if c.isdigit() or c in '.:').strip('.:')
        value_reads.append(keep)
    rows = {}
    for i, k in enumerate(key_reads):
        if not k or k == 'none' or k in rows:
            continue
        rows[k] = (value_reads[i] if i < len(value_reads) and value_reads[i] else 'nothing')
    if not rows:
        return {'seq': 'none', 'refused': True,
                'verdict': 'no printed key came back from any cut-out -> abstain rather than '
                           'zero the card'}
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'n': len(rows), 'verdict': 'the page reads back as %s' % seq}


def onefield(node):
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
    """The first word read from the cut out; refuse when nothing usable is read."""
    field = onefield(node)
    words = [x for x in str(field.get('val') or '').split() if x]
    if field.get('refused') or not words or words[0] == 'none':
        return {'val': 'none', 'refused': True,
                'verdict': 'no usable word came back from that cut-out -> abstain rather than '
                           'zero the card'}
    return {'val': words[0], 'verdict': 'the reader answers %s' % words[0]}


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

# end of code_read
