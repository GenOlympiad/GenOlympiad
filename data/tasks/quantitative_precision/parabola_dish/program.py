# code: parab_code
def parabola_fit_score(focus_read, directrix_read, mark_read, image, reference):
    """Score how close each magenta point's focus to directrix distance ratio is to one."""
    import math
    W, H = image.size
    out = {'frac': 0.0, 'n_pts': 0, 'ratios': None, 'dev': None, 'degenerate': True}
    fy, fx = [float(v) for v in focus_read['geometry'][:2]]
    fx, fy = fx * W / 1000.0, fy * H / 1000.0
    y0, x0, y1, x1 = [float(v) for v in directrix_read['geometry'][0][:4]]
    ax, bx = x0 * W / 1000.0, x1 * W / 1000.0
    ay, by = y0 * H / 1000.0, y1 * H / 1000.0
    dx, dy = abs(bx - ax), abs(by - ay)
    horiz = dx >= dy
    L = max(dx, dy)
    cx, cy = (ax + bx) / 2.0, (ay + by) / 2.0
    min_pts = int(reference['min_pts'])
    boxes = list(mark_read.get('geometry') or [])
    out['n_pts'] = len(boxes)
    if L < 20.0 or len(boxes) < min_pts:
        return out
    ratios = []
    for b in boxes:
        py0, px0, py1, px1 = [float(v) for v in b[:4]]
        px = ((px0 + px1) / 2.0) * W / 1000.0
        py = ((py0 + py1) / 2.0) * H / 1000.0
        focus_dist = math.hypot(px - fx, py - fy)
        directrix_dist = abs(py - cy) if horiz else abs(px - cx)
        if directrix_dist < 1.0:
            continue
        ratios.append(focus_dist / directrix_dist)
    if len(ratios) < min_pts:
        return out
    deviation = math.sqrt(sum((r - 1.0) ** 2 for r in ratios) / len(ratios))
    tolerance = float(reference['tol'])
    return {'frac': round(max(0.0, 1.0 - deviation / (2.0 * tolerance)), 4), 'dev': round(deviation, 4),
            'n_pts': len(ratios), 'ratios': [round(r, 3) for r in ratios], 'degenerate': False}

# end of parab_code
