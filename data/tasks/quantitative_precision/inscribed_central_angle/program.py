# code: ratio2_code
def vertex_angle(vp, bx, W, H):
    import math, itertools
    boxes = [[float(v) for v in b] for b in (bx or {}).get('geometry') or []]
    if len(boxes) != 2:
        return None
    cor = []
    for y0, x0, y1, x1 in boxes:
        cor.append([(x * W / 1000.0, y * H / 1000.0)
                    for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))])
    best, bs = None, None
    for f in itertools.product(range(4), repeat=2):
        d = math.dist(cor[0][f[0]], cor[1][f[1]])
        if bs is None or d < bs:
            bs, best = d, f
    inner = [cor[0][best[0]], cor[1][best[1]]]
    vx = sum(q[0] for q in inner) / 2.0
    vy = sum(q[1] for q in inner) / 2.0
    src = 'ray_inner_ends'
    g = [float(v) for v in ((vp or {}).get('geometry') or [])]
    if (vp or {}).get('confirmed') and len(g) == 2:
        vx, vy = g[1] * W / 1000.0, g[0] * H / 1000.0
        src = 'confirmed_point'
    dirs = []
    for cs in cor:
        tip = max(cs, key=lambda q: math.hypot(q[0] - vx, q[1] - vy))
        dx, dy = tip[0] - vx, -(tip[1] - vy)
        if math.hypot(dx, dy) < 0.05 * max(W, H):
            return None
        dirs.append(math.degrees(math.atan2(dy, dx)))
    a = abs(dirs[0] - dirs[1]) % 360.0
    if a > 180.0:
        a = 360.0 - a
    return {'deg': a, 'vertex_px': [vx, vy], 'vertex_source': src,
            'inner_spread_px': round(bs, 1)}


def angle_ratio_score(central_point, central_boxes, inscribed_point, inscribed_boxes, src, reference):
    """Score how close the central angle is to twice the inscribed angle."""
    W, H = src.size
    A = vertex_angle(central_point, central_boxes, W, H)
    B = vertex_angle(inscribed_point, inscribed_boxes, W, H)
    bad = {'frac': 0.0, 'ang_a': None, 'ang_b': None, 'measured_ratio': None,
           'err': None, 'confirmed': False, 'degenerate': True}
    if A is None or B is None or B['deg'] < 3.0:
        return bad
    target = float(reference['ratio'])
    tol = float(reference['tol'])
    measured_ratio = A['deg'] / B['deg']
    err = abs(measured_ratio - target) / abs(target)
    return {'frac': round(max(0.0, 1.0 - err / (2.5 * tol)), 4),
            'ang_a': round(A['deg'], 2), 'ang_b': round(B['deg'], 2),
            'measured_ratio': round(measured_ratio, 3), 'target_ratio': round(target, 3),
            'err': round(err, 3), 'deg_off': round(abs(A['deg'] - target * B['deg']), 1),
            'central_vertex_source': A['vertex_source'],
            'inscribed_vertex_source': B['vertex_source'],
            'confirmed': True, 'degenerate': False}

# end of ratio2_code
