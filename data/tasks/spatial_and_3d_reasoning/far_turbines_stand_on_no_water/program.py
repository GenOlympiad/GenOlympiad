# code: helpers
from genolympiad.task_helpers import sweep_banned_unless_count_disagrees
# end of helpers

# shared code: code_hull
def _one(node):
    for raw in (node or {}).get('answers') or []:
        t = ' '.join(str(raw or '').lower().split()).strip(' .,:-')
        if t and t != 'none':
            return t
    return ''
def _all(node):
    out = []
    for raw in (node or {}).get('answers') or []:
        out.append(' '.join(str(raw or '').lower().split()).strip(' .,:-'))
    return out
def _num(t):
    keep = ''
    neg = False
    s = str(t or '')
    for i, ch in enumerate(s):
        if ch.isdigit() or ch == '.':
            keep += ch
        elif ch == '-' and not keep:
            neg = True
        elif keep:
            break
    try:
        v = float(keep)
    except ValueError:
        return None
    return -v if neg else v
def _head(t):
    w = str(t or '').split()
    return w[0] if w else ''
def _norm(t):
    keep = ''
    for ch in str(t or '').lower():
        if ch.isalnum():
            keep += ch
    return keep
def _rawone(node):
    for raw in (node or {}).get('answers') or []:
        t = str(raw or '').strip()
        if t and t.lower() != 'none':
            return t
    return ''
def _lines(node):
    out = []
    for raw in (node or {}).get('answers') or []:
        for part in str(raw or '').replace('\r', '\n').split('\n'):
            t = ' '.join(part.split()).strip()
            if t:
                out.append(t)
    return out
def _first(node):
    a = _all(node)
    return a[0] if a else ''
def _yes(t):
    return _norm(t).startswith('yes')
def _no(t):
    h = _norm(t)
    return h.startswith('no') or h.startswith('none') or h.startswith('nothing')
def _hold(msg, **extra):
    d = {'tag': 'no', 'refused': True, 'verdict': msg}
    d.update(extra)
    return d
def _say(ok, msg, **extra):
    d = {'tag': 'yes' if ok else 'no', 'refused': False, 'verdict': msg}
    d.update(extra)
    return d

def _cut(t):
    w = _norm(t)
    if 'only' in w or 'nacelle' in w or 'rotor' in w or w.startswith('top'):
        return 'top'
    if 'most' in w or 'cut' in w:
        return 'most'
    if 'whole' in w or 'meetsthesea' in w or w.startswith('all'):
        return 'whole'
    return None


def towers_visible_match(node, expect):
    """Yes if the tower count above the horizon matches what the distances allow."""
    v = _num(_one(node))
    if v is None:
        return _hold('the count of towers standing above the horizon did not come back '
                     '-> abstain')
    return _say(abs(v - float(expect)) < 0.5,
                'the reader counts %s towers above the horizon and the four listed distances '
                'leave %s of them showing' % (v, expect), read=v)


def towers_cut_match(a, b, c, expect):
    """Yes if each of the three towers is cut by the horizon as the reference says."""
    got = [_cut(_one(a)), _cut(_one(b)), _cut(_one(c))]
    if any(g is None for g in got):
        return _hold('one of the three towers did not come back as one of the three offered '
                     'answers -> abstain', got=got)
    want = list(expect)
    return _say(got == want,
                'the three towers read %s and the distances give %s' % (got, want), got=got)


def no_sea_below_towers(middle_read, far_read):
    """Yes if no sea shows under the bases of the middle and far towers."""
    middle_answer, far_answer = _norm(_one(middle_read)), _norm(_one(far_read))
    if not middle_answer or not far_answer:
        return _hold('one of the two waterline questions did not come back -> abstain')
    for t in (middle_answer, far_answer):
        if not (t.startswith('yes') or t.startswith('no')):
            return _hold('a waterline question came back as %s, which is neither yes nor no '
                         '-> abstain' % t)
    return _say(middle_answer.startswith('no') and far_answer.startswith('no'),
                'sea showing under the middle tower: %s; under the far tower: %s' % (middle_answer, far_answer),
                mid=middle_answer, far=far_answer)

# end of code_hull
