# code: converge_code
import math


def vanishing_scatter(reads, dirs, src):
    """How tightly the red nosing lines meet in one point, as a share of the image diagonal."""
    boxes_read = (reads or {}).get('geometry') or []
    answers = (dirs or {}).get('answers') or []
    W, H = src.size
    if len(boxes_read) < 3 or len(answers) != len(boxes_read):
        return {'scatter_frac': None, 'n_segs': len(boxes_read), 'unreadable': True, 'refused': True}
    lines = []
    for b, a in zip(boxes_read, answers):
        y0, x0, y1, x1 = [float(v) for v in b[:4]]
        word = str(a or '').strip().lower()
        px0, px1 = x0 * float(W) / 1000.0, x1 * float(W) / 1000.0
        py0, py1 = y0 * float(H) / 1000.0, y1 * float(H) / 1000.0
        if 'up' in word:
            p, q = (px0, py1), (px1, py0)
        elif 'down' in word:
            p, q = (px0, py0), (px1, py1)
        else:
            continue
        if abs(q[0] - p[0]) < 1.0 and abs(q[1] - p[1]) < 1.0:
            continue
        lines.append((p, q))
    if len(lines) < 3:
        return {'scatter_frac': None, 'n_segs': len(lines), 'unreadable': True, 'refused': True}
    crossings = []
    for i in range(len(lines)):
        for jj in range(i + 1, len(lines)):
            (ax, ay), (bx, by) = lines[i]
            (cx, cy), (dx, dy) = lines[jj]
            rx, ry = bx - ax, by - ay
            sx, sy = dx - cx, dy - cy
            den = rx * sy - ry * sx
            if abs(den) < 1e-9:
                continue
            t = ((cx - ax) * sy - (cy - ay) * sx) / den
            crossings.append((ax + t * rx, ay + t * ry))
    if not crossings:
        return {'scatter_frac': None, 'n_segs': len(lines), 'unreadable': True}
    diag = math.sqrt(float(W) ** 2 + float(H) ** 2)
    xs = sorted(p[0] for p in crossings)
    ys = sorted(p[1] for p in crossings)
    mx = xs[len(xs) // 2]
    my = ys[len(ys) // 2]
    keep = [p for p in crossings if math.hypot(p[0] - mx, p[1] - my) < 5.0 * diag]
    if not keep:
        return {'scatter_frac': None, 'n_segs': len(lines), 'unreadable': True}
    rms = math.sqrt(sum((p[0] - mx) ** 2 + (p[1] - my) ** 2 for p in keep) / float(len(keep)))
    return {'scatter_frac': round(rms / diag, 4), 'n_segs': len(lines),
            'focus': [round(mx / float(W), 4), round(my / float(H), 4)], 'unreadable': False}

# end of converge_code
