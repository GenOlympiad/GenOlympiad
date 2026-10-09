# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, map_answer_to_token
# end of helpers

# shared code: code_sides
def count_nuts_in_b_half(nuts, band, letter, letter_read, want):
    """Count the walnuts whose centre lies in the B half of the printed band."""
    def _box(b):
        try:
            v = [float(x) for x in list(b)[:4]]
        except Exception:
            return None
        if len(v) != 4:
            return None
        y0, x0, y1, x1 = min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3])
        return None if (y1 <= y0 or x1 <= x0) else [y0, x0, y1, x1]

    def _geo(node):
        return [r for r in (_box(b) for b in ((node or {}).get('geometry') or [])) if r]

    def _held(why):
        return {'state': 'off', 'n': None, 'n_nuts': None, 'no_read': True, 'refused': True,
                'verdict': why}

    def _miss(why, n_nuts):
        return {'state': 'off', 'n': None, 'n_nuts': n_nuts, 'no_read': False,
                'verdict': why}

    nut_boxes, band_boxes, letter_boxes = _geo(nuts), _geo(band), _geo(letter)
    if not band_boxes:
        return _held('the printed band was never located, so the two halves are undefined')
    if not letter_boxes:
        return _held('no stencilled letter was located at all')
    b = [min(r[0] for r in band_boxes), min(r[1] for r in band_boxes),
         max(r[2] for r in band_boxes), max(r[3] for r in band_boxes)]
    axis = 1 if (b[2] - b[0]) > (b[3] - b[1]) else 0
    lo, hi = b[axis], b[axis + 2]

    def _side(box):
        c = 0.5 * (box[axis] + box[axis + 2])
        return 'before' if c < lo else ('after' if c > hi else 'on_band')

    letter_answers = [str(a).strip().lower()[:1] for a in ((letter_read or {}).get('answers') or [])]
    seen = {}
    on_band = 0
    for box, a in zip(letter_boxes, letter_answers):
        if a not in ('a', 'b'):
            continue
        s = _side(box)
        if s == 'on_band':
            on_band += 1
            continue
        seen.setdefault(a, set()).add(s)
    if on_band and not seen:
        return _miss('every stencilled letter is printed ON the band, not one in each half, '
                     'so the picture never made the two halves the prompt asked for', len(nut_boxes))
    if 'a' not in seen and 'b' not in seen:
        return _miss('no stencilled letter could be placed in either half', len(nut_boxes))
    sides_a = seen.get('a') or set()
    sides_b = seen.get('b') or set()
    if len(sides_a) > 1 or len(sides_b) > 1:
        return _miss('the same letter is stencilled in BOTH halves, so the halves are not the '
                     'A half and the B half the prompt asked for', len(nut_boxes))
    if sides_a and sides_b and sides_a == sides_b:
        return _miss('the A and the B are stencilled in the SAME half, so the picture never made '
                     'an A half and a B half', len(nut_boxes))
    if sides_b:
        b_side = list(sides_b)[0]
    else:
        b_side = 'after' if list(sides_a)[0] == 'before' else 'before'
    n_in_b = sum(1 for r in nut_boxes if _side(r) == b_side)
    ok = (len(nut_boxes) == 9 and n_in_b == int(want))
    return {'state': 'match' if ok else 'off', 'n': n_in_b, 'n_nuts': len(nut_boxes),
            'no_read': False,
            'verdict': '%d of the %d walnuts have their centre in the B half' % (n_in_b, len(nut_boxes))}

# end of code_sides

# shared code: code_clear
def none_on_line(node):
    """Check that all nine walnuts read as clear of the band edge."""
    answers = [str(a).strip().lower()[:1] for a in (node or {}).get('answers') or []]
    n_touching = sum(1 for a in answers if a == 'y')
    ok = len(answers) == 9 and n_touching == 0
    return {'state': 'match' if ok else 'off', 'n': n_touching,
            'verdict': '%d of %d walnuts sit on the line' % (n_touching, len(answers))}

# end of code_clear
