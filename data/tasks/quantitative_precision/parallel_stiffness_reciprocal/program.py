# code: recip_code
def combined_travel_score(g, o, b, src, reference):
    """Score how close the blue bar is to the reciprocal sum of the green and orange bars."""
    import math
    W, H = src.size
    def blen(node):
        bs = list(node.get('geometry') or [])
        if not bs:
            return 0.0
        y0, x0, y1, x1 = [float(v) for v in bs[0][:4]]
        return math.hypot((x1 - x0) * W / 1000.0, (y1 - y0) * H / 1000.0)
    green_len, orange_len, blue_len = blen(g), blen(o), blen(b)
    if min(green_len, orange_len, blue_len) < 5.0:
        return {'frac': 0.0, 'x1': None, 'x2': None, 'x_eq': None, 'expected': None,
                'err': None, 'degenerate': True}
    expected = (green_len * orange_len) / (green_len + orange_len)
    if expected < 1.0:
        return {'frac': 0.0, 'x1': None, 'x2': None, 'x_eq': None, 'expected': None,
                'err': None, 'degenerate': True}
    tol = float(reference['tol'])
    err = abs(blue_len - expected) / expected
    return {'frac': round(max(0.0, 1.0 - err / (2.5 * tol)), 4),
            'x1': round(green_len / W, 4), 'x2': round(orange_len / W, 4), 'x_eq': round(blue_len / W, 4),
            'expected': round(expected / W, 4), 'err': round(err, 3), 'degenerate': False}

# end of recip_code
