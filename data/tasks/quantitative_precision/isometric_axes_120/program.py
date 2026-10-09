# code: isoset_code
def isometric_angle_score(l1, l2, l3, src, reference):
    """Score the worst gap between the three traced edge angles and the target angles."""
    import math
    W, H = src.size
    targets = [float(a) for a in reference['target_angles']]
    tol = float(reference['tol'])
    bad = {'frac': 0.0, 'angles': None, 'best_err': None, 'deg_off': None,
           'confirmed': False, 'degenerate': True, 'refused': True}

    def read(node):
        g = (node or {}).get('geometry')
        if not g:
            return None
        v = list(g[0]) if isinstance(g[0], (list, tuple)) else list(g)
        if len(v) < 4:
            return None
        y0, x0, y1, x1 = [float(t) for t in v[:4]]
        p0 = (x0 * W / 1000.0, y0 * H / 1000.0)
        p1 = (x1 * W / 1000.0, y1 * H / 1000.0)
        dx, dy = p1[0] - p0[0], -(p1[1] - p0[1])
        if math.hypot(dx, dy) < 0.04 * max(W, H):
            return None
        return (math.degrees(math.atan2(dy, dx)) % 180.0, v)

    reads = [read(l1), read(l2), read(l3)]
    if any(r is None for r in reads):
        return bad
    angles = [r[0] for r in reads]
    used = [False] * len(angles)
    worst, wj = 0.0, 0
    for a_t in targets:
        bestd, bj = 1e9, -1
        for k, a in enumerate(angles):
            if used[k]:
                continue
            dd = abs(a - a_t)
            dd = min(dd, 180.0 - dd)
            if dd < bestd:
                bestd, bj = dd, k
        if bj >= 0:
            used[bj] = True
            if bestd > worst:
                worst, wj = bestd, bj
        else:
            worst = 180.0
    return {'frac': round(max(0.0, 1.0 - worst / (2.5 * tol)), 4),
            'angles': [round(a, 2) for a in angles], 'best_err': round(worst, 2),
            'deg_off': round(worst, 1), 'junction_source': 'traced_edges',
            'geometry': reads[wj][1],
            'verdict': 'edges measured at %s deg against %s -> worst error %.1f deg'
                       % ([round(a, 1) for a in angles], [round(t, 1) for t in targets], worst),
            'confirmed': True, 'degenerate': False}

# end of isoset_code
