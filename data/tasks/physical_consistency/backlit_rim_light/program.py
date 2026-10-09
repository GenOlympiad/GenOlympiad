# code: norm_side_code

def norm_side(sd):
    """Reduce the side answer to left, right, both, neither or none."""
    t = str(sd).lower()
    for tok in ('left', 'right', 'both', 'neither'):
        if tok in t:
            return tok
    return 'none'

# end of norm_side_code

# code: far_dark_code
def rim_light_side(rim, animal):
    """Which fur edge of the animal carries the vetted rim-light patches: left, right, both or none."""
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

    animal_boxes = _geo(animal)
    if not animal_boxes:
        return {'state': 'off', 'lit_side': None, 'n_rim': None, 'no_read': True, 'refused': True,
                'verdict': 'the animal was never located, so its two fur edges are undefined'}
    a = animal_boxes[0]
    mid = 0.5 * (a[1] + a[3])
    tol = 0.05 * (a[3] - a[1])
    rim_boxes = _geo(rim)
    left = right = 0
    for r in rim_boxes:
        centre_x = 0.5 * (r[1] + r[3])
        if abs(centre_x - mid) <= tol:
            continue
        if centre_x < mid:
            left += 1
        else:
            right += 1
    if rim_boxes and left == 0 and right == 0:
        return {'state': 'off', 'lit_side': None, 'n_rim': len(rim_boxes), 'no_read': True,
                'refused': True,
                'verdict': 'every rim patch sits astride the animal, so which fur edge carries '
                           'the glow cannot be told from the geometry'}
    if not rim_boxes:
        side = 'none'
    elif left and right:
        side = 'both'
    else:
        side = 'left' if left else 'right'
    return {'state': 'off' if (left and right) else 'match', 'lit_side': side, 'n_rim': len(rim_boxes),
            'verdict': '%d rim patches vetted: %d along one fur edge, %d along the other'
                       % (len(rim_boxes), left, right)}

# end of far_dark_code
