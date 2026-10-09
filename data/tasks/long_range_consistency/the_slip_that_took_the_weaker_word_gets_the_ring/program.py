# code: helpers
from genolympiad.task_helpers import sweep_banned_unless_count_disagrees
# end of helpers

# shared code: code_main
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




def _words(t):
    out, cur = [], ''
    for ch in str(t or '').lower():
        if ch.isalnum():
            cur += ch
        elif cur:
            out.append(cur)
            cur = ''
    if cur:
        out.append(cur)
    return out


def _pick(t, table):
    hit = set()
    for w in _words(t):
        for name, pres in table.items():
            for p in pres:
                if w.startswith(p):
                    hit.add(name)
    return hit.pop() if len(hit) == 1 else None



def _side(t):
    return _pick(t, {'first': ('first', '1st'), 'second': ('second', '2nd'),
                     'third': ('third', '3rd'), 'fourth': ('fourth', '4th')})


_ORD = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4}


def inked_slip_check(which, howmany, want):
    """Say yes when the ink mark sits on the reference slip and is the only one on the desk."""
    slip_side, mark_count = _side(_one(which)), _num(_one(howmany))
    if slip_side is None or mark_count is None:
        return _hold('the which-slip question or the how-many question did not come back '
                     '-> abstain', ringed=slip_side, rings=mark_count)
    return _say(_ORD[slip_side] == int(want) and int(mark_count) == 1,
                'the ink ring is round slip %d and there are %d ring(s) on the desk, and the '
                'review leaves exactly one slip to send back'
                % (_ORD[slip_side], int(mark_count)), ringed=_ORD[slip_side], rings=int(mark_count), expected=int(want))


def annotation_word_check(hand, stamp, want):
    """Say yes when the handwritten word is the reference word and differs from the stamp."""
    handwritten, stamped = _norm(_one(hand)), _norm(_one(stamp))
    if not handwritten or not stamped:
        return _hold('the handwritten word or the stamped word did not come back -> abstain',
                     handwritten=handwritten, stamped=stamped)
    return _say(handwritten == _norm(want) and handwritten != stamped,
                'the reviewer wrote %s beside a slip stamped %s, and the word that should have '
                'been stamped is the stronger of the two notices' % (handwritten, stamped),
                handwritten=handwritten, stamped=stamped, expected=_norm(want))


def named_case_stamp_check(case, stamp, want_case, want_word):
    """Say yes when the slip for the asked case is stamped with the reference word."""
    case_number, stamped = _num(_one(case)), _norm(_one(stamp))
    if case_number is None or not stamped:
        return _hold('the case number or the stamped word did not come back -> abstain',
                     case=case_number, stamped=stamped)
    if int(case_number) != int(want_case):
        return _hold('the cut-out landed on case %d, not the case this leg asks about '
                     '-> abstain' % int(case_number), case=int(case_number), wanted_case=int(want_case))
    return _say(stamped == _norm(want_word),
                'the slip for case %d is stamped %s, and the notice it names gives the stronger '
                'word for that case' % (int(case_number), stamped), case=int(case_number), stamped=stamped,
                expected=_norm(want_word))

# end of code_main
