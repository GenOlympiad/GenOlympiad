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


def _flat(t):
    out = ''
    for c in str(t or '').lower():
        out += c if c.isalnum() else ' '
    return ' ' + ' '.join(out.split()) + ' '


def _pick(t, opts):
    s = _flat(t)
    hits = []
    for o in sorted(opts, key=len, reverse=True):
        if (' ' + o + ' ') in s:
            keep = True
            for h in hits:
                if o in h:
                    keep = False
            if keep:
                hits.append(o)
    return hits[0] if len(hits) == 1 else None


EMPTY_WORDS = ['none', 'blank', 'empty', 'nothing', 'no time', 'no figure', 'no number',
               'no name', 'no date', 'no month', 'not printed', 'no text', 'no word']


def _empty(t):
    return _pick(t, EMPTY_WORDS) is not None


def _nums(t):
    raw, cur = [], ''
    for c in str(t or '') + ' ':
        if c.isdigit() or (c == '.' and cur and cur[-1].isdigit()):
            cur += c
        elif c == ',' and cur and cur[-1].isdigit():
            continue
        elif c == ':' and cur and cur[-1].isdigit():
            cur += ':'
        else:
            if cur:
                raw.append(cur)
            cur = ''
    vals = []
    for s in raw:
        s = s.rstrip('.').rstrip(':')
        if s:
            vals.append(s)
    return vals


def _one_num(node, what):
    a = answer_texts(node)
    if len(a) != 1:
        return None, withheld_result('%d readings came back for %s, so no single figure stands there'
                              % (len(a), what))
    if _empty(a[0]):
        return 'none', None
    v = [x for x in _nums(a[0]) if ':' not in x]
    if len(v) != 1:
        return None, withheld_result('%d figures were made out for %s: %r' % (len(v), what, a[0]))
    try:
        return float(v[0]), None
    except ValueError:
        return None, withheld_result('the figure for %s did not parse: %r' % (what, a[0]))


def _one_clock(node, what):
    a = answer_texts(node)
    if len(a) != 1:
        return None, withheld_result('%d readings came back for %s' % (len(a), what))
    if _empty(a[0]):
        return 'none', None
    v = [x for x in _nums(a[0]) if ':' in x]
    if len(v) != 1:
        return None, withheld_result('%d clock times were made out for %s: %r' % (len(v), what, a[0]))
    p = v[0].split(':')
    if len(p) != 2 or not p[0].isdigit() or not p[1].isdigit():
        return None, withheld_result('the time for %s did not parse: %r' % (what, a[0]))
    return '%02d:%02d' % (int(p[0]), int(p[1])), None


def _one_word(node, opts, what):
    a = answer_texts(node)
    if len(a) != 1:
        return None, withheld_result('%d readings came back for %s' % (len(a), what))
    if _empty(a[0]):
        return 'none', None
    g = _pick(a[0], opts)
    if g is None:
        return None, withheld_result('the answer for %s was not one of the words offered: %r'
                              % (what, a[0]))
    return g, None


def _one_yesno(node, what):
    a = answer_texts(node)
    if len(a) != 1:
        return None, withheld_result('%d readings came back for %s' % (len(a), what))
    g = _pick(a[0], ['yes', 'yeah', 'yep', 'correct', 'no', 'nope', 'none'])
    if g is None:
        return None, withheld_result('the answer for %s was neither a yes nor a no: %r' % (what, a[0]))
    return ('no' if g in ('no', 'nope', 'none') else 'yes'), None


def _caps(t):
    out = ''
    for c in str(t or ''):
        if ('a' <= c <= 'z') or ('A' <= c <= 'Z'):
            out += c.upper()
    return out


def _one_word_letters(node, want_len, what):
    a = answer_texts(node)
    if len(a) != 1:
        return None, withheld_result('%d readings came back for %s' % (len(a), what))
    if _empty(a[0]):
        return 'none', None
    s = _caps(a[0])
    if len(s) < want_len:
        return None, withheld_result('only %d letters of the %d %s carries came back: %r'
                              % (len(s), want_len, what, a[0]))
    return s, None
CLUBS = ['wharf', 'kilns', 'draymen']


def spoon_club(reads):
    """Pass when the spoon holder's top names Kilns, the side that scored fewest."""
    g, bad = _one_word(reads, CLUBS, 'the club name on the top of the player holding the spoon')
    if bad is not None:
        return bad
    return yes_no_result(g == 'kilns',
                'the spoon is held by %s, against the side that scored fewest across the three '
                'drawn matches' % g)


def bench_club(reads):
    """Pass when the benched player's top names Wharf, the side that scored most."""
    g, bad = _one_word(reads, CLUBS, 'the club name on the top of the player on the bench')
    if bad is not None:
        return bad
    return yes_no_result(g == 'wharf',
                'the bench carries %s, against the side that scored most across the three drawn '
                'matches' % g)

# end of code_card
