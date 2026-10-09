# code: helpers
from genolympiad.task_helpers import (
    compare_transcribed_marks, count_listed_items, sweep_banned_unless_count_disagrees)
# end of helpers

# shared code: code_card
def answer_texts(node):
    return [' '.join(str(a or '').split()).strip() for a in (node or {}).get('answers') or []]


def _abstain(why):
    return {'tag': 'none', 'n': None, 'refused': True, 'verdict': why}


def _tag(tag, why):
    return {'tag': tag, 'refused': False, 'verdict': why}


def _words(t):
    return ''.join(c if c.isalnum() else ' ' for c in str(t or '').lower()).split()


def _head(v):
    return ' '.join(str(v or '').split()).lower().lstrip(' .,:;*_([')


NEG = ('not', 'no', 'never', 'neither', 'without', 'nor')


def _choose(text, opts):
    ws = _words(text)
    hits, denied = [], False
    for i in range(len(ws)):
        if ws[i] in NEG:
            denied = True
            continue
        if denied:
            continue
        for tag, keys in opts:
            if any(ws[i].startswith(k) for k in keys):
                if tag not in hits:
                    hits.append(tag)
                break
    return hits[0] if len(hits) == 1 else None


def _one(node, what):
    a = answer_texts(node)
    if len(a) == 1:
        return a[0], None
    return None, _abstain('%d readings came back for %s, so there is no single answer to '
                          'judge -> abstain rather than zero the card' % (len(a), what))


def match_offered_word(node, pool, what):
    """Match the one answer to exactly one offered word, skipping negated words."""
    a, ab = _one(node, what)
    if ab is not None:
        return ab
    opts = []
    for p in str(pool).split('|'):
        p = p.strip().lower()
        if p:
            opts.append((p, (p[:4],)))
    g = _choose(a, opts)
    if g is None:
        return _abstain('the reading for %s named none of the answers offered, or named two '
                        'of them: %r' % (what, a))
    return _tag(g, '%s reads back as %s' % (what, g))


def yesno(node, what):
    a, ab = _one(node, what)
    if ab is not None:
        return ab
    h = _head(a)
    if h.startswith('yes'):
        return _tag('yes', '%s reads back as yes' % what)
    if h.startswith('no') or h.startswith('none') or h.startswith('nothing'):
        return _tag('no', '%s reads back as no' % what)
    return _abstain('the reading for %s was neither yes nor no: %r' % (what, a))


WORDNUM = {'zero': 0, 'none': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
           'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}


def _digits(s):
    out, cur = [], ''
    for ch in str(s or ''):
        if ch.isdigit():
            cur += ch
        elif cur:
            out.append(int(cur))
            cur = ''
    if cur:
        out.append(int(cur))
    return out


HEDGE = ('or', 'maybe', 'perhaps', 'either', 'possibly', 'about', 'roughly')


def _tally(text):
    d = _digits(text)
    if len(d) == 1:
        return d[0]
    if d:
        return None
    ws = _words(text)
    spoken = [WORDNUM[x] for x in ws if x in WORDNUM]
    if not spoken:
        return None
    if any(h in ws for h in HEDGE):
        return None
    if len(spoken) == 1 or (ws and ws[0] in WORDNUM):
        return spoken[0]
    return None


def read_count(node, what):
    """Read a single count from the one answer, else refuse."""
    a, ab = _one(node, what)
    if ab is not None:
        return ab
    n = _tally(a)
    if n is None:
        return _abstain('no single tally came back for %s: %r' % (what, a))
    return {'n': n, 'refused': False, 'verdict': '%s comes back as %d' % (what, n)}


def read_figure(node, what):
    """Read the single figure in a box, or 'none' if it was left empty, else refuse."""
    a, ab = _one(node, what)
    if ab is not None:
        return ab
    h = _head(a)
    if h == '':
        return _abstain('nothing at all came back for %s, which is evidence about the reader '
                        'and not about the page -> abstain rather than zero the card' % what)
    if h.startswith('none') or h.startswith('nothing') or h.startswith('empty'):
        return {'n': 'none', 'refused': False, 'verdict': '%s was left with no figure in it' % what}
    n = _tally(a)
    if n is None:
        return _abstain('no single figure was made out in %s: %r' % (what, a))
    return {'n': n, 'refused': False, 'verdict': '%s reads %d' % (what, n)}


def money(node, what):
    a, ab = _one(node, what)
    if ab is not None:
        return ab
    h = _head(a)
    if h == '':
        return _abstain('nothing at all came back for %s, which is evidence about the reader '
                        'and not about the page -> abstain rather than zero the card' % what)
    if h.startswith('none') or h.startswith('nothing') or h.startswith('empty'):
        return {'n': 'none', 'refused': False, 'verdict': '%s carries no figure at all' % what}
    buf = ''
    for ch in str(a):
        if ch.isdigit() or ch == '.':
            buf += ch
        elif ch == ',':
            continue
        elif buf:
            buf += ' '
    parts = []
    for p in buf.split():
        if any(c.isdigit() for c in p):
            parts.append(p)
    if len(parts) != 1:
        return _abstain('%d money figures were made out on %s: %r' % (len(parts), what, a))
    try:
        v = float(parts[0])
    except ValueError:
        return _abstain('the figure on %s could not be read as an amount: %r' % (what, a))
    return {'n': int(round(v * 100)), 'refused': False,
            'verdict': '%s reads %s' % (what, parts[0])}


def pair(one, two, what_a, what_b):
    x = money(one, what_a)
    if x.get('refused'):
        return x
    y = money(two, what_b)
    if y.get('refused'):
        return y
    if x['n'] == 'none' or y['n'] == 'none':
        return _tag('no', 'one of the two figures was left off the page altogether')
    same = x['n'] == y['n']
    return _tag('yes' if same else 'no',
                '%s and %s read %s and %s' % (what_a, what_b, x['verdict'], y['verdict']))

# end of code_card
