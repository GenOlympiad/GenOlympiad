# code: helpers
from genolympiad.task_helpers import sweep_banned_unless_count_disagrees
# end of helpers

# shared code: code_card
def answer_texts(node):
    return [' '.join(str(a or '').split()).strip() for a in (node or {}).get('answers') or []]


def _norm(t):
    s = str(t or '').lower()
    for ch in '-.,:;!"()[]' + chr(39):
        s = s.replace(ch, ' ')
    return ' ' + ' '.join(s.split()) + ' '


def _pick(t, table):
    s = _norm(t)
    best = None
    for tag, words in table:
        for w in words:
            if (' ' + w + ' ') in s and (best is None or len(w) > best[1]):
                best = (tag, len(w))
    return best[0] if best else None


def _digits(t):
    return ''.join(c for c in str(t or '') if c.isdigit())


def _words(t):
    s = _norm(t)
    return ''.join(c for c in s if c.isalpha() or c == ' ').split()


def withheld_result(why):
    return {'tag': 'none', 'refused': True, 'verdict': why}


def yes_no_result(ok, why):
    return {'tag': 'yes' if ok else 'no', 'refused': False, 'verdict': why}


def _all(vals):
    return None not in vals and len(vals) > 0


def _nums(t):
    out, cur = [], ''
    for ch in str(t or '') + ' ':
        if ch.isdigit():
            cur += ch
        else:
            if cur:
                out.append(int(cur))
            cur = ''
    return out


SHP = (('wider', ('wider', 'broader', 'opens out', 'flares', 'bigger at the top',
                  'wider at the top')),
       ('same', ('same', 'same width', 'parallel', 'straight', 'equal', 'the same width')),
       ('narrower', ('narrower', 'tapers in', 'smaller at the top', 'narrower at the top')))
ANSWER = 8


def _one_num(node, what):
    v = [_nums(x) for x in answer_texts(node)]
    if len(v) != 1 or not v[0]:
        return None, withheld_result('the cut-out did not come back with %s -> abstain rather than zero '
                              'the card' % what)
    return v[0][-1], None


def load_level_ok(level_read):
    """Whether the load stands level with the mark the plated payload allows."""
    n, stop = _one_num(level_read, 'the number of the mark the load is level with')
    if stop:
        return stop
    return yes_no_result(n == ANSWER, 'the load stands at mark %d where the plated payload allows mark %d'
                % (n, ANSWER))


def mark_matches_label(level_read, label_read):
    """Whether the mark the load reaches equals the mark number printed on the label."""
    a, stop = _one_num(level_read, 'the number of the mark the load is level with')
    if stop:
        return stop
    b, stop = _one_num(label_read, 'the mark number printed on the card')
    if stop:
        return stop
    return yes_no_result(a == b, 'the section is loaded to mark %d and the card says mark %d' % (a, b))


def taper(shape_read):
    """Whether the body is read as wider at the top than at its floor."""
    shapes = [_pick(x, SHP) for x in answer_texts(shape_read)]
    if len(shapes) != 1 or not _all(shapes):
        return withheld_result('the cut-out did not say how the top of the body compares with its floor '
                        '-> abstain rather than zero the card')
    return yes_no_result(shapes[0] == 'wider', 'the body reads %s at the top than at the floor' % shapes[0])

# end of code_card
