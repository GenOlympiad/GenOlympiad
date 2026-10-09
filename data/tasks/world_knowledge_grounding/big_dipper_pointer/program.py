# shared code: code_d9f91a8de3cb

def image_size(p):
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
    return 1000.0, 1000.0


def _fit(src, dst):
    n = len(src)
    if n < 2 or len(dst) != n:
        return None, None
    mx = sum(p[0] for p in src) / n
    my = sum(p[1] for p in src) / n
    nx = sum(p[0] for p in dst) / n
    ny = sum(p[1] for p in dst) / n
    S = [(p[0] - mx, p[1] - my) for p in src]
    D = [(p[0] - nx, p[1] - ny) for p in dst]
    a = sum(S[i][0] * D[i][0] + S[i][1] * D[i][1] for i in range(n))
    b = sum(S[i][0] * D[i][1] - S[i][1] * D[i][0] for i in range(n))
    den = sum(S[i][0] ** 2 + S[i][1] ** 2 for i in range(n))
    if den <= 1e-9:
        return None, None
    c, s = a / den, b / den
    rs = 0.0
    for i in range(n):
        fx = c * S[i][0] - s * S[i][1] + nx
        fy = s * S[i][0] + c * S[i][1] + ny
        rs += (fx - dst[i][0]) ** 2 + (fy - dst[i][1]) ** 2
    rms = (rs / n) ** 0.5
    sd = (sum(D[i][0] ** 2 + D[i][1] ** 2 for i in range(n)) / n) ** 0.5 or 1.0

    def tf(p):
        px, py = p[0] - mx, p[1] - my
        return (c * px - s * py + nx, s * px + c * py + ny)
    return tf, rms / sd


def _yes(a):
    return str(a).strip().lower().startswith('y')


def place_polaris(stars, checks, image, reference):
    """Score where Polaris sits on the pointer line after fitting the Dipper shape."""
    import itertools
    geometry = (stars or {}).get('geometry') or []
    answers = (checks or {}).get('answers') or []
    keep = [geometry[i] for i in range(len(geometry)) if i < len(answers) and _yes(answers[i])]
    n_body = int(reference['n_body'])
    W, H = image_size(image) if isinstance(image, str) else (1000.0, 1000.0)
    pts = []
    for bx in keep:
        if not bx or len(bx) < 4:
            continue
        y0, x0, y1, x1 = [float(v) for v in bx[:4]]
        cy = (y0 + y1) / 2.0 * H / 1000.0
        cx = (x0 + x1) / 2.0 * W / 1000.0
        area = abs(y1 - y0) * abs(x1 - x0)
        pts.append((area, cx, H - cy))
    if len(pts) < n_body + 1:
        return {'ratio': None, 'perp': None, 'body': None, 'place': 0.0, 'n_stars': len(pts),
                'n_proposed': len(geometry), 'no_read': True,
                'why': 'fewer individually-confirmed bright stars than the asterism needs'}
    pts.sort(key=lambda t: -t[0])
    cand = [(p[1], p[2]) for p in pts[:n_body + 1]]
    cat = [[float(c[0]), float(c[1])] for c in reference['catalog']]
    best = None
    for drop in range(n_body + 1):
        body = [cand[k] for k in range(n_body + 1) if k != drop]
        bp = None
        for order in itertools.permutations(range(n_body)):
            tf, rms = _fit([cat[o] for o in order], body)
            if rms is None:
                continue
            if bp is None or rms < bp[0]:
                bp = (rms, tf)
        if bp is None:
            continue
        if best is None or bp[0] < best[0]:
            best = (bp[0], bp[1], cand[drop])
    if best is None:
        return {'ratio': None, 'perp': None, 'body': None, 'place': 0.0, 'n_stars': len(pts),
                'no_read': True, 'why': 'no valid registration'}
    body_rms, tf, polaris_point = best
    ptr = [int(v) for v in reference['pointer']]
    frm = tf(cat[ptr[0]])
    to = tf(cat[ptr[1]])
    vx, vy = to[0] - frm[0], to[1] - frm[1]
    L2 = vx * vx + vy * vy
    if L2 <= 1e-9:
        return {'ratio': None, 'perp': None, 'body': round(body_rms, 4), 'place': 0.0,
                'n_stars': len(pts), 'no_read': True, 'why': 'degenerate pointer pair'}
    dx, dy = polaris_point[0] - frm[0], polaris_point[1] - frm[1]
    ratio = (dx * vx + dy * vy) / L2
    perp = ((dx - ratio * vx) ** 2 + (dy - ratio * vy) ** 2) ** 0.5 / (L2 ** 0.5)
    tr = float(reference['target_ratio'])
    fr = max(0.0, 1.0 - max(0.0, abs(ratio - tr) - 0.6) / 2.4)
    fp = max(0.0, 1.0 - max(0.0, abs(perp - 0.0) - 0.25) / 0.75)
    place = round(fr * fp, 4)
    ex = frm[0] + tr * vx
    ey = frm[1] + tr * vy
    def _pm(x, y):
        return [(H - y) * 1000.0 / H, x * 1000.0 / W]
    p0, p1 = _pm(frm[0], frm[1]), _pm(to[0], to[1])
    pc = _pm(ex, ey)
    rad = 0.6 * (L2 ** 0.5) * 1000.0 / min(W, H)
    return {'ratio': round(ratio, 3), 'perp': round(perp, 3), 'body': round(body_rms, 4),
            'place': place, 'n_stars': len(pts), 'no_read': False,
            'ray': {'confirmed': True, 'geometry': [p0[0], p0[1], p1[0], p1[1]]},
            'circ': {'confirmed': True, 'geometry': [pc[0], pc[1], rad]},
            'verdict': 'ratio %.2f (want %.2f) perp %.2f shape_rms %.3f -> place frac %.3f'
                       % (ratio, tr, perp, body_rms, place)}

# end of code_d9f91a8de3cb
