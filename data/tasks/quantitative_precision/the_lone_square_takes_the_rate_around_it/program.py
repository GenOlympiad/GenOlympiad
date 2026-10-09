# code: helpers
from genolympiad.task_helpers import sweep_banned_unless_count_disagrees
# end of helpers

# shared code: code_vra
def answer_texts(node):
    return [' '.join(str(a or '').split()).strip() for a in (node or {}).get('answers') or []]


def _one(node):
    for t in answer_texts(node):
        if t and t.lower() != 'none':
            return t
    return ''


def answer_head(t):
    return str(t or '').strip().lower().lstrip('*_"\'.,:;-([ ')


def _alnum(t):
    return ''.join(c for c in str(t or '').lower() if c.isalnum())


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


def _word(t, opts):
    parts = answer_head(t).split()
    h = parts[0].strip('*_"\'.,:;-([)') if parts else ''
    for o in opts:
        if h.startswith(str(o)[:3]):
            return o
    return None


def withheld_result(why):
    return {'tag': 'none', 'refused': True, 'verdict': why}


def yes_no_result(ok, why):
    return {'tag': 'yes' if ok else 'no', 'refused': False, 'verdict': why}


RATES = (15.0, 30.0, 45.0)


def check_legend_rates(swatches, values):
    """Check the legend lists exactly the three rates the map uses, abstaining on unread lines."""
    n = len((swatches or {}).get('geometry') or [])
    a = answer_texts(values)
    got, miss = [], 0
    for i in range(n):
        r = leading_number(a[i] if i < len(a) else '')
        if r is None:
            miss += 1
        else:
            got.append(r)
    if not n or miss:
        return withheld_result('%d of %d legend lines did not read back a rate -> abstain, '
                        'do not book a model zero' % (miss, n))
    s = set(got)
    return yes_no_result(s == set(RATES), 'legend carries ' + ','.join('%g' % r for r in sorted(s))
                + ' | the map only uses ' + ','.join('%g' % r for r in sorted(RATES)))


def odd_squares_absorbed(a, b):
    """Check both odd squares read as the same rate as the squares around them."""
    x = _word(_one(a), ('same', 'different'))
    y = _word(_one(b), ('same', 'different'))
    if x is None or y is None:
        return withheld_result('an odd square did not read back a same or different answer '
                        '-> abstain, do not book a model zero')
    return yes_no_result(x == 'same' and y == 'same',
                'first odd square reads %s, second reads %s' % (x, y))

# end of code_vra
