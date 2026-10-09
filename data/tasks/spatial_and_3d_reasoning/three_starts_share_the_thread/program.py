# code: helpers
from genolympiad.task_helpers import sweep_banned_unless_count_disagrees
# end of helpers

# shared code: code_card
def answer_texts(node):
    return [' '.join(str(a or '').split()).strip() for a in (node or {}).get('answers') or []]


def answer_head(t):
    return str(t or '').strip().lower().lstrip('*_"\'.,:;-([ ')


def first_option_word(t, opts):
    parts = answer_head(t).split()
    h = parts[0].strip('*_"\'.,:;-()[]') if parts else ''
    for o in opts:
        if h and h.startswith(str(o)[:3]):
            return o
    return None


def leading_number(t):
    keep, seen = '', False
    for c in str(t or ''):
        if c.isdigit():
            keep += c
        elif c == '.' and not seen and keep:
            keep += c
            seen = True
        elif keep:
            break
    try:
        return float(keep)
    except ValueError:
        return None


def _alnum(t):
    return ''.join(c for c in str(t or '').lower() if c.isalnum())


def withheld_result(why):
    return {'tag': 'none', 'refused': True, 'verdict': why}


def yes_no_result(ok, why):
    return {'tag': 'yes' if ok else 'no', 'refused': False, 'verdict': why}


def _n_boxes(node):
    node = node or {}
    try:
        n = int(node.get('n_confirmed') or 0)
    except Exception:
        n = 0
    return n or len(list(node.get('geometry') or []))


def three_thread_starts(read):
    """Whether the judge VLM counted exactly three ridges starting at the rim."""
    n = leading_number(answer_texts(read)[0] if answer_texts(read) else '')
    if n is None:
        return withheld_result('the number of thread starts did not read back')
    return yes_no_result(int(n) == 3, '%d ridges begin at the rim' % int(n))


def ridges_cross(read):
    """Whether the ridges were reported to cross or merge."""
    word = first_option_word(answer_texts(read)[0] if answer_texts(read) else '', ('yes', 'no'))
    if word is None:
        return withheld_result('whether the ridges meet did not read back')
    return {'tag': word, 'refused': False, 'verdict': 'ridges cross or merge: %s' % word}


def three_starts_inside_closure(read):
    """Whether exactly three ridges start inside the closure."""
    n = leading_number(answer_texts(read)[0] if answer_texts(read) else '')
    if n is None:
        return withheld_result('the number of ridges inside the closure did not read back')
    return yes_no_result(int(n) == 3, '%d ridges begin inside the closure' % int(n))

# end of code_card
