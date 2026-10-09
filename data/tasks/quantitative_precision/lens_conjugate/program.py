# code: conj_code
def thin_lens_fit(lens, obj, img, foc, reference):
    """Score how well object, image and focal distances fit the thin lens equation."""
    def pt_x(node):
        if not (node or {}).get('confirmed'):
            return None
        g = (node or {}).get('geometry') or []
        try:
            g = [float(q) for q in g]
        except Exception:
            return None
        return g[1] if len(g) == 2 else None

    def box_cx(node):
        gs = (node or {}).get('geometry') or []
        if not gs:
            return None
        b = [float(q) for q in gs[0]]
        return (b[1] + b[3]) / 2.0

    bad = {'frac': 0.0, 'degenerate': True, 'u': None, 'v': None, 'f': None, 'err': None}
    lens_x = pt_x(lens)
    if lens_x is None:
        return dict(bad, verdict='degenerate: the lens-plane point was not confirmed')
    object_x, image_x = box_cx(obj), box_cx(img)
    if object_x is None or image_x is None:
        return dict(bad, verdict='degenerate: an arrow box was not confirmed')
    dots = [(float(b[1]) + float(b[3])) / 2.0 for b in ((foc or {}).get('geometry') or [])]
    if not dots:
        return dict(bad, verdict='degenerate: no focal-point dot was confirmed')
    focal_x = min(dots, key=lambda q: abs(q - lens_x))
    side = 'left' if focal_x < lens_x else 'right'
    u = abs(object_x - lens_x)
    v = abs(image_x - lens_x)
    f = abs(focal_x - lens_x)
    if u < 3.0 or v < 3.0 or f < 3.0:
        return dict(bad, u=round(u, 1), v=round(v, 1), f=round(f, 1),
                    verdict='degenerate: a mark sits on the lens plane itself')
    lhs = 1.0 / u + 1.0 / v
    rhs = 1.0 / f
    err = abs(lhs - rhs) / rhs
    tol = float(reference['tol'])
    frac = max(0.0, 1.0 - err / (2.5 * tol))
    return {'frac': round(frac, 4), 'degenerate': False, 'u': round(u, 1), 'v': round(v, 1),
            'f': round(f, 1), 'err': round(err, 3), 'dots_confirmed': len(dots),
            'f_side': side,
            'verdict': 'lens plane read at x=%.0f; u=%.0f v=%.0f f=%.0f (per-mille of frame '
                       'width, f to the %s focal dot) -> 1/u+1/v = %.5f vs 1/f = %.5f '
                       '(%.1f%% off) -> frac %.2f'
                       % (lens_x, u, v, f, side, lhs, rhs, 100.0 * err, frac)}

# end of conj_code
