# shared code: gridcode
def grid_spacing_error(centers, rows, cols):
    """The worst relative deviation of any dot gap from its row or column mean gap."""
    R, C = int(rows), int(cols)
    if centers is None or len(centers) != R*C:
        return 1.0
    points = [(float(a), float(b)) for a, b in centers]
    points.sort(key=lambda p: p[1])
    grid = []
    for i in range(R):
        row = sorted(points[i*C:(i+1)*C], key=lambda p: p[0])
        grid.append(row)
    worst = 0.0
    for row in grid:
        xs = [p[0] for p in row]
        gaps = [xs[k+1]-xs[k] for k in range(len(xs)-1)]
        if not gaps:
            continue
        m = sum(gaps)/len(gaps)
        if m <= 0:
            return 1.0
        worst = max(worst, max(abs(g-m)/m for g in gaps))
    for c in range(C):
        ys = [grid[i][c][1] for i in range(R)]
        gaps = [ys[k+1]-ys[k] for k in range(len(ys)-1)]
        if not gaps:
            continue
        m = sum(gaps)/len(gaps)
        if m <= 0:
            return 1.0
        worst = max(worst, max(abs(g-m)/m for g in gaps))
    return round(worst, 4)

# end of gridcode

# code: count_yes_code
def count_yes(node):
    """Count the yes answers among the per dot checks."""
    answers = (node or {}).get('answers') or []
    yes = [a for a in answers if str(a or '').strip().lower().startswith('yes')]
    return {'n': len(yes), 'asked': len(answers), 'answers': [str(a) for a in answers],
            'why': 'one atomic yes/no per confirmed rectangle, summed in code'}

# end of count_yes_code

# code: centres_code
def centres(boxes, source):
    """The pixel centre of each confirmed registration dot box."""
    W, H = source.size
    geometry = (boxes or {}).get('geometry') or []
    centers = []
    for b in geometry:
        y0, x0, y1, x1 = [float(v) for v in b]
        centers.append([(x0 + x1) / 2.0 * W / 1000.0, (y0 + y1) / 2.0 * H / 1000.0])
    return {'centers': centers, 'n': len(centers), 'degenerate': len(centers) < 4,
            'why': 'centre of each confirmed dot rectangle, in pixels'}

# end of centres_code
