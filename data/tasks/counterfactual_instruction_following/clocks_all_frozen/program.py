# code: headcount_code

def all_clocks_match(cr, reference):
    """Score 1 only if the expected number of boxes was found and every one reads the time."""
    import re
    OPP = {'top': 'bottom', 'bottom': 'top', 'wick': 'flame', 'flame': 'wick',
           'back': 'face', 'face': 'back', 'left': 'right', 'right': 'left'}
    g = dict(reference or {})
    expected_values = [str(v) for k, v in sorted(g.items())
            if k.startswith('exp_') and k != 'exp_item']
    if expected_values and len(set(expected_values)) != 1:
        return {'frac': 0.0, 'verdict': 'authored per-item expectations are not uniform'}
    want = g.get('exp_item')
    if want is None:
        want = expected_values[0] if expected_values else None
    n_want = g.get('n_objects')
    if n_want is None:
        n_want = len(expected_values)
    n_want = int(n_want)
    w = str(want).strip().lower()

    def match(a):
        s = str(a or '').strip().lower()
        if re.match(r'^\d+$', w):
            v = [int(x) for x in re.findall(r'\d+', s) if 1 <= int(x) <= 12]
            return bool(v) and v[0] == int(w)
        mk = re.search(r'\b%s\b' % re.escape(w), s)
        opp = OPP.get(w)
        mo = re.search(r'\b%s\b' % re.escape(opp), s) if opp else None
        return bool(mk) and (mo is None or mk.start() < mo.start())

    answers = (cr or {}).get('answers') or []
    n_boxes = len(answers)
    n_match = sum(1 for a in answers if match(a))
    frac = 1.0 if (n_boxes == n_want and n_boxes and n_match == n_boxes) else 0.0
    return {'frac': frac, 'n_boxes': n_boxes, 'n_match': n_match, 'n_want': n_want,
            'want': w, 'answers': [str(a) for a in answers],
            'verdict': '%d of %d confirmed boxes read "%s" (%d demanded) -> frac %.1f'
                       % (n_match, n_boxes, w, n_want, frac)}

# end of headcount_code
