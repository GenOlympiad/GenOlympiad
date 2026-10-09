# code: snell_code
def width_height(p):
    try:
        with open(p, 'rb') as f:
            head = f.read(32)
        if head[:8] == b'\x89PNG\r\n\x1a\n':
            import struct
            w, h = struct.unpack('>II', head[16:24])
            if w > 0 and h > 0:
                return float(w), float(h)
    except Exception:
        pass
    return 1.0, 1.0


def _vec(node, W, H):
    import math
    g = (node or {}).get('geometry')
    if not g or len(g) < 4:
        return None
    y0, x0, y1, x1 = [float(v) for v in g[:4]]
    dx = (x1 - x0) * W / 1000.0
    dy = (y1 - y0) * H / 1000.0
    return None if math.hypot(dx, dy) < 8.0 else (dx, dy)


def sine_ratio_score(ray_in, ray_out, reference, image):
    """Score how closely the sine ratio of the drawn ray angles matches the refractive index."""
    import math
    W, H = width_height(image) if isinstance(image, str) else (1.0, 1.0)
    dir_in, dir_out = _vec(ray_in, W, H), _vec(ray_out, W, H)
    out = {'frac': 0.0, 'degenerate': False, 'ang_in': None, 'ang_out': None,
           'sine_ratio': None, 'target': None, 'err': None}
    if dir_in is None or dir_out is None:
        out['degenerate'] = out['refused'] = True
        return out
    normal_deg = float(reference.get('normal_deg', 90.0) or 90.0)
    nx, ny = math.cos(math.radians(normal_deg)), -math.sin(math.radians(normal_deg))
    nn = math.hypot(nx, ny) or 1.0

    def to_normal(d):
        m = math.hypot(d[0], d[1])
        c = abs((d[0] * nx + d[1] * ny) / (m * nn))
        return math.degrees(math.acos(min(1.0, max(0.0, c))))

    angle_in, angle_out = to_normal(dir_in), to_normal(dir_out)
    sin_out = math.sin(math.radians(angle_out))
    out['ang_in'], out['ang_out'] = round(angle_in, 2), round(angle_out, 2)
    if sin_out < 1e-3:
        out['degenerate'] = True
        return out
    ratio = math.sin(math.radians(angle_in)) / sin_out
    target = float(reference['n'])
    if target <= 1e-6:
        out['degenerate'] = True
        return out
    tol = float(reference.get('tol', 0.14) or 0.14)
    err = abs(ratio - target) / target
    out.update({'sine_ratio': round(ratio, 3), 'target': round(target, 3),
                'err': round(err, 3), 'frac': round(max(0.0, 1.0 - err / (2.5 * tol)), 4)})
    return out

# end of snell_code
