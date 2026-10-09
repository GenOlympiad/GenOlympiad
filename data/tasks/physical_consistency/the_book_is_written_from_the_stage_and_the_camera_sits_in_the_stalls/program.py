# code: helpers
from genolympiad.task_helpers import sweep_banned_unless_count_disagrees
# end of helpers

# shared code: code_card
def answer_texts(node):
    return [' '.join(str(a or '').split()).strip() for a in (node or {}).get('answers') or []]


def withheld_result(why):
    return {'tag': 'none', 'refused': True, 'verdict': why}


def yes_no_result(ok, why):
    return {'tag': 'yes' if ok else 'no', 'refused': False, 'verdict': why}


def _toks(t):
    return ''.join(c if c.isalnum() else ' ' for c in str(t or '').lower()).split()


def _word(t, opts):
    ts = _toks(t)
    if 'not' in ts or 'neither' in ts:
        return None
    hits = []
    for w in ts:
        for o in sorted(opts, key=len, reverse=True):
            if w.startswith(o[:3]) and o not in hits:
                hits.append(o)
                break
    return hits[0] if len(hits) == 1 else None


def _nums(t):
    raw, cur, vals = [], '', []
    for c in str(t or '') + ' ':
        if c.isdigit() or (c == '.' and cur and cur[-1].isdigit()):
            cur += c
        elif c == ',' and cur and cur[-1].isdigit():
            continue
        else:
            if cur:
                raw.append(cur)
            cur = ''
    for s in raw:
        s = s.rstrip('.')
        if s:
            vals.append(float(s))
    return vals


def _one_num(node, what):
    a = answer_texts(node)
    if len(a) != 1:
        return None, withheld_result('%d readings came back for %s, so no single figure exists there'
                              % (len(a), what))
    if _word(a[0], ['none', 'blank']) is not None:
        return 'none', None
    n = _nums(a[0])
    if len(n) != 1:
        return None, withheld_result('%d figures were made out for %s: %r' % (len(n), what, a[0]))
    return n[0], None


def _one_word(node, opts, what):
    a = answer_texts(node)
    if len(a) != 1:
        return None, withheld_result('%d readings came back for %s' % (len(a), what))
    g = _word(a[0], opts)
    if g is None:
        return None, withheld_result('the answer for %s was not one of the words offered: %r'
                              % (what, a[0]))
    return g, None


def _n_yes(node):
    a = answer_texts(node)
    yes = 0
    uns = 0
    for x in a:
        h = str(x).lower().lstrip('*_"\'.,:;- (')
        if h.startswith('yes') or h.startswith('yep') or h.startswith('yeah') or h == 'y':
            yes += 1
        elif h.startswith('no') or h.startswith('nope') or h == 'n':
            pass
        else:
            uns += 1
    return len(a), yes, uns


def _many_nums(node, what):
    a = answer_texts(node)
    if len(a) != 1:
        return None, withheld_result('%d readings came back for %s' % (len(a), what))
    if _word(a[0], ['none', 'blank']) is not None:
        return [], None
    v = _nums(a[0])
    if not v:
        return None, withheld_result('no figure at all was made out on %s: %r' % (what, a[0]))
    return v, None

def raised_arm_side(reads):
    """Yes if the actor with the raised arm is read as standing on the left."""
    g, bad = _one_word(reads, ['left', 'right'], 'the pair of actors')
    if bad is not None:
        return bad
    return yes_no_result(g == 'left',
                'the actor with the raised arm stands to the %s of the other one' % g)


def raised_arm_between(reads):
    """Yes if the raised arm is read as between the two actors."""
    g, bad = _one_word(reads, ['between', 'outside'], 'the raised arm')
    if bad is not None:
        return bad
    return yes_no_result(g == 'between', 'the raised arm reads as the one %s the two of them' % g)


def arms_down_further(reads):
    """Yes if the actor with both arms down is read as further from the camera."""
    g, bad = _one_word(reads, ['nearer', 'further'], 'the actor with both arms down')
    if bad is not None:
        return bad
    return yes_no_result(g == 'further',
                'the actor with both arms down reads as the %s of the two from the camera' % g)

# end of code_card
