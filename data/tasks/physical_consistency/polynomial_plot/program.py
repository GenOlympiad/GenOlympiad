# code: poly_shape_code
def poly_shape(shape_node, end_node, tail_node, reference):
    """Check the read turning point, lower end and right end slope against the reference curve."""
    points = [[float(p[0]), float(p[1])] for p in (reference.get('curve') or [])]
    if len(points) < 5:
        return {'frac': 0.0, 'unread': True, 'verdict': 'no spec curve'}
    ys = [p[1] for p in points]
    xs = [p[0] for p in points]
    last = len(points) - 1
    want_shape = 'straight'
    prev = None
    for i in range(1, len(ys)):
        d = ys[i] - ys[i - 1]
        if d == 0:
            continue
        s = 1 if d > 0 else -1
        if prev is not None and s != prev:
            want_shape = 'peak' if prev > 0 else 'trough'
            break
        prev = s
    want_low = 'left' if ys[0] < ys[last] else 'right'
    span = xs[last] - xs[0]
    yr = max(ys) - min(ys)
    tail = [p for p in points if p[0] >= xs[last] - 0.10 * span] or points[-2:]
    slope_frac = abs(tail[-1][1] - tail[0][1]) / yr if yr else 0.0
    want_tail = 'flat' if slope_frac < 0.08 else 'steep'
    def first(node):
        a = (node or {}).get('answers') or []
        return str(a[0] if a else '').strip().lower()
    a1, a2, a3 = first(shape_node), first(end_node), first(tail_node)
    def pick(a, words):
        hit, at = None, -1
        for w in words:
            i = a.rfind(w)
            if i > at:
                hit, at = w, i
        return hit
    got_shape = pick(a1, ('peak', 'trough', 'straight'))
    got_low = pick(a2, ('left', 'right'))
    got_tail = pick(a3, ('flat', 'steep'))
    if got_shape is None or got_low is None or got_tail is None:
        return {'frac': 0.0, 'unread': True,
                'verdict': 'unparsable shape reads (%s / %s / %s)' % (a1, a2, a3)}
    ok = (got_shape == want_shape) and (got_low == want_low) and (got_tail == want_tail)
    return {'frac': 1.0 if ok else 0.0, 'unread': False,
            'shape': got_shape, 'want_shape': want_shape,
            'lower_end': got_low, 'want_lower_end': want_low,
            'right_end': got_tail, 'want_right_end': want_tail,
            'spec_tail_slope_frac': round(slope_frac, 4),
            'verdict': 'curve reads %s / lower end %s / right end %s; spec says %s / %s / %s -> frac %.1f' % (got_shape, got_low, got_tail, want_shape, want_low, want_tail,
                  1.0 if ok else 0.0)}

# end of poly_shape_code
