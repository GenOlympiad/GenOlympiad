# code: tilt_code
def _ends(node):
    g = (node or {}).get('geometry')
    if not g:
        return None
    v = list(g[0]) if isinstance(g[0], (list, tuple)) else list(g)
    if len(v) < 4:
        return None
    return [float(t) for t in v[:4]]


import math


def book_tilt_from_wall(reads, src):
    """Measure the book's lean from the wall in degrees from its read end-to-end line."""
    end_points = _ends(reads)
    if end_points is None:
        return {'from_wall': None, 'no_read': True, 'refused': True}
    y0, x0, y1, x1 = end_points
    W, H = src.size
    dy = abs(y1 - y0) * float(H) / 1000.0
    dx = abs(x1 - x0) * float(W) / 1000.0
    if dy < 2.0 and dx < 2.0:
        return {'from_wall': None, 'no_read': True, 'refused': True}
    from_floor = math.degrees(math.atan2(dy, max(dx, 1e-6)))
    return {'from_wall': round(90.0 - from_floor, 2), 'from_floor': round(from_floor, 2),
            'no_read': False}

# end of tilt_code
