# shared code: code_e2babd360d22

def expected_star_circles(m, pb, reference_steps):
    """Predict where each star should sit in later panels from the reference turns."""
    import math
    out = []
    if not isinstance(m, dict) or m.get('unreadable'):
        return {'circles': [], 'W': 1.0, 'H': 1.0, 'n': 0}
    W, H = float(pb['W']), float(pb['H'])
    steps = [float(s) for s in (reference_steps or [])]
    radii = (m.get('radii') or [[]])[0]
    ang = (m.get('ang') or [[]])[0]
    poles = m.get('poles') or []
    if not radii or not ang or len(poles) < 2:
        return {'circles': [], 'W': W, 'H': H, 'n': 0}
    for i in range(1, len(poles)):
        turn = sum(steps[:i]) if len(steps) >= i else 0.0
        ox, oy = poles[i]
        for r, a0 in zip(radii, ang):
            a = math.radians(a0 + turn)
            x, y = ox + r * math.cos(a), oy - r * math.sin(a)
            out.append([x / W, y / H, 0.030])
    return {'circles': out, 'W': W, 'H': H, 'n': len(out)}


def corners(pb):
    """The four corner points of the full image."""
    return [[0.0, 0.0], [float(pb['W']), 0.0], [float(pb['W']), float(pb['H'])],
            [0.0, float(pb['H'])]]

# end of code_e2babd360d22

# shared code: code_3ac265e20c76

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


def panel_boxes(image, n_panels, axis):
    """Split the page into equal panel boxes along the given axis."""
    n = int(n_panels)
    W, H = width_height(image) if isinstance(image, str) else (1.0, 1.0)
    out = {'n': n, 'W': W, 'H': H, 'axis': axis}
    for i in range(3):
        j = min(i, n - 1)
        if axis == 'tb':
            b = [0.0, j / float(n), 1.0, (j + 1) / float(n)]
        else:
            b = [j / float(n), 0.0, (j + 1) / float(n), 1.0]
        out['p%d' % i] = b
    return out


def _centres(ring, box, pb):
    if not isinstance(ring, dict) or ring.get('refused') or not ring.get('geometry'):
        return None
    W, H = float(pb['W']), float(pb['H'])
    x0, y0, x1, y1 = [float(v) for v in box]
    cw, ch = (x1 - x0) * W, (y1 - y0) * H
    pts = []
    for g in ring['geometry']:
        v = [float(t) for t in list(g)[:4]]
        if len(v) < 4:
            return None
        cy, cx = 0.5 * (v[0] + v[2]), 0.5 * (v[1] + v[3])
        pts.append((x0 * W + cx / 1000.0 * cw, y0 * H + cy / 1000.0 * ch))
    return pts


def _template_proposal(ring):
    g = (ring or {}).get('geometry') or []
    if len(g) < 3:
        return False
    sizes = set()
    for b in g:
        v = [float(t) for t in list(b)[:4]]
        sizes.add((round(v[3] - v[1], 3), round(v[2] - v[0], 3)))
    return len(sizes) == 1


def _centres_multi(rings, box, pb):
    ok = []
    for r in rings or []:
        if _template_proposal(r):
            continue
        pts = _centres(r, box, pb)
        if pts is not None:
            ok.append(pts)
    if not ok:
        return None
    if len(set(len(p) for p in ok)) > 1:
        return 'disagree'
    return ok[0]


def _pole(ring, box, pb):
    if not isinstance(ring, dict) or ring.get('refused') or not ring.get('geometry'):
        return None
    g = ring['geometry']
    if isinstance(g[0], (list, tuple)):
        g = g[0]
    W, H = float(pb['W']), float(pb['H'])
    x0, y0, x1, y1 = [float(v) for v in box]
    cw, ch = (x1 - x0) * W, (y1 - y0) * H
    cy, cx = float(g[0]), float(g[1])
    return (x0 * W + cx / 1000.0 * cw, y0 * H + cy / 1000.0 * ch)


def _median(xs):
    s = sorted(float(x) for x in xs)
    n = len(s)
    if not n:
        return 0.0
    m = n // 2
    return s[m] if n % 2 else 0.5 * (s[m - 1] + s[m])


def _pct(xs, q):
    s = sorted(float(x) for x in xs)
    n = len(s)
    if not n:
        return 0.0
    if n == 1:
        return s[0]
    pos = (q / 100.0) * (n - 1)
    lo = int(pos)
    hi = min(lo + 1, n - 1)
    return s[lo] + (pos - lo) * (s[hi] - s[lo])


def sky_fit(image, n_panels, axis, pb, r0, r1, r2, p0, p1, p2):
    """Measure the star field turn about the pole between each pair of panels."""
    import math
    n = int(n_panels)
    rings = [r0, r1, r2][:n]
    poles = [p0, p1, p2][:n]
    boxes = [pb['p0'], pb['p1'], pb['p2']][:n]
    stars, pole_points = [], []
    for i in range(n):
        pts = _centres_multi(rings[i], boxes[i], pb)
        pol = _pole(poles[i], boxes[i], pb)
        if pts == 'disagree':
            return {'unreadable': True, 'reason': 'panel_%d_wordings_disagree' % i,
                    'steps_deg': [], 'counts': []}
        if pts is None or pol is None or len(pts) < 3:
            return {'unreadable': True,
                    'reason': 'panel_%d_%s' % (i, 'no_stars' if pts is None or len(pts) < 3
                                               else 'no_pole'),
                    'steps_deg': [], 'counts': []}
        stars.append(pts)
        pole_points.append(pol)
    counts = [len(s) for s in stars]
    polar = []
    for i in range(n):
        ox, oy = pole_points[i]
        pts = []
        for x, y in stars[i]:
            dx, dy = x - ox, -(y - oy)
            pts.append((math.hypot(dx, dy), math.degrees(math.atan2(dy, dx))))
        pts.sort(key=lambda t: t[0])
        polar.append(pts)
    steps, spreads, shape, scale = [], [], [], []
    for i in range(n - 1):
        A, B = polar[i], polar[i + 1]
        ratios, dth = [], []
        for j in range(min(len(A), len(B))):
            if A[j][0] < 1e-6:
                continue
            ratios.append(B[j][0] / A[j][0])
            dth.append((B[j][1] - A[j][1] + 180.0) % 360.0 - 180.0)
        if len(dth) < 3:
            return {'unreadable': True, 'reason': 'degenerate_pairs',
                    'steps_deg': [], 'counts': counts}
        sn = sum(math.sin(math.radians(d)) for d in dth) / float(len(dth))
        cs = sum(math.cos(math.radians(d)) for d in dth) / float(len(dth))
        s = math.degrees(math.atan2(sn, cs))
        dev = [abs((d - s + 180.0) % 360.0 - 180.0) for d in dth]
        med = _median(ratios)
        steps.append(round(s, 2))
        spreads.append(round(_pct(dev, 75), 2))
        shape.append(round(_pct([abs(x / med - 1.0) for x in ratios], 75), 4))
        scale.append(round(abs(med - 1.0), 4))
    return {'unreadable': False, 'n_panels': n, 'counts': counts, 'steps_deg': steps,
            'spread_deg': spreads, 'shape_err': shape, 'scale_err': scale,
            'poles': [[round(c[0], 1), round(c[1], 1)] for c in pole_points],
            'radii': [[round(p[0], 1) for p in pp] for pp in polar],
            'ang': [[round(p[1], 2) for p in pp] for pp in polar]}

# end of code_3ac265e20c76

# code: f_code
def same_star_counts(counts, want):
    """Score 1 when every panel shows the same number of stars, at least four."""
    c = list(counts or [])
    return 1.0 if (len(c) == int(want) and len(set(c)) == 1
                   and min(c) >= 4) else 0.0

# end of f_code

# code: f_code_2
def band(x, core, marg):
    e = abs(float(x))
    if e <= core: return 1.0
    if e >= marg: return 0.0
    return (marg - e) / (marg - core)
def rigid_turn_score(shape, scale, spread):
    """Score how closely each panel pair fits a pure turn in shape, scale and spread."""
    shapes, scales, spreads = list(shape or []), list(scale or []), list(spread or [])
    if not shapes or len(scales) != len(shapes) or len(spreads) != len(shapes): return 0.0
    v = [min(band(shapes[i], 0.12, 0.32), band(scales[i], 0.14, 0.38),
             band(spreads[i], 12.0, 35.0)) for i in range(len(shapes))]
    return round(min(v), 4)

# end of f_code_2

# code: f_code_3
def band(x, core, marg):
    e = abs(float(x))
    if e <= core: return 1.0
    if e >= marg: return 0.0
    return (marg - e) / (marg - core)
def turn_step_score(got, want):
    """Score each measured turn between panels against its reference turn, averaged."""
    g, w = list(got or []), list(want or [])
    if not w or len(g) != len(w): return 0.0
    t = 0.0
    for i in range(len(w)):
        e = abs((float(g[i]) - float(w[i]) + 180.0) % 360.0 - 180.0)
        t += band(e, 8.0, 25.0)
    return round(t / len(w), 4)

# end of f_code_3

# code: f_code_4
def turn_direction_share(got, want):
    """The share of turns between panels going the reference way by at least 12 degrees."""
    g, w = list(got or []), list(want or [])
    if not w or len(g) != len(w): return 0.0
    ok = 0
    for i in range(len(w)):
        if float(g[i]) * float(w[i]) > 0 and abs(float(g[i])) >= 12.0:
            ok += 1
    return round(float(ok) / len(w), 4)

# end of f_code_4
