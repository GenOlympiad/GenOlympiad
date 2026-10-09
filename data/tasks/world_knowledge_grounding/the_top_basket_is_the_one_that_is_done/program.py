# code: helpers
from genolympiad.task_helpers import map_answer_to_token, sweep_banned_unless_count_disagrees
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


SKIN = (('clear', ('clear', 'translucent', 'see through', 'shows the filling', 'transparent',
                   'glassy', 'you can see the filling', 'the pink filling shows through')),
        ('milky', ('milky', 'opaque', 'white', 'milky white', 'solid white', 'pale')))
SWELL = (('swollen', ('swollen', 'swelled', 'puffed', 'plump', 'risen', 'pressed together',
                      'pressed up against', 'touching', 'full', 'puffed up')),
         ('apart', ('apart', 'gaps', 'gap', 'not touching', 'spaced', 'room between',
                    'still apart', 'separate')))
GLOSS = (('glossy', ('glossy', 'shiny', 'wet looking', 'sheen', 'glistening', 'wet')),
         ('floury', ('floury', 'dull', 'matt', 'powdery', 'dry looking', 'chalky', 'dry')))


def _two(a, b, table, what):
    x = [_pick(v, table) for v in answer_texts(a)]
    y = [_pick(v, table) for v in answer_texts(b)]
    if len(x) != 1 or len(y) != 1 or not _all(x) or not _all(y):
        return None, withheld_result('both baskets did not come back saying %s (%s, %s) -> abstain '
                              'rather than zero the card' % (what, x, y))
    return (x[0], y[0]), None


def compare_skins(top_skin, bottom_skin):
    """Check the top basket reads clear skins and the bottom basket milky ones."""
    got, stop = _two(top_skin, bottom_skin, SKIN, 'how the skin looks')
    if stop:
        return stop
    return yes_no_result(got == ('clear', 'milky'),
                'the top basket reads %s and the bottom basket reads %s' % got)


def compare_swelling(top_swell, bottom_swell):
    """Check the top basket reads swollen dumplings and the bottom basket spaced ones."""
    got, stop = _two(top_swell, bottom_swell, SWELL, 'whether the dumplings have swelled')
    if stop:
        return stop
    return yes_no_result(got == ('swollen', 'apart'),
                'the top basket reads %s and the bottom basket reads %s' % got)


def compare_surfaces(middle_gloss, bottom_gloss):
    """Check the middle basket reads glossy and the bottom basket floury."""
    got, stop = _two(middle_gloss, bottom_gloss, GLOSS, 'how the surface looks')
    if stop:
        return stop
    return yes_no_result(got == ('glossy', 'floury'),
                'the middle basket reads %s and the bottom basket reads %s' % got)

# end of code_card
