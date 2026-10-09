# code: aspects_code
import math


def _px_box(b, W, H):
    y0, x0, y1, x1 = [float(v) for v in b[:4]]
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0,
            abs(y1 - y0) * float(H) / 1000.0, abs(x1 - x0) * float(W) / 1000.0)


def _angles(rd, src):
    g = (rd or {}).get('geometry') or []
    W, H = src.size
    rows = []
    for b in g:
        cx, cy, h, w = _px_box(b, W, H)
        if h < 2.0 and w < 2.0:
            return None
        rows.append((cx, math.degrees(math.atan2(h, max(w, 1e-6)))))
    rows.sort()
    return [a for _, a in rows]


def ellipse_aspects(reads, src):
    """Height to width ratio of each tabletop ellipse, and the spread between them."""
    boxes = (reads or {}).get('geometry') or []
    W, H = src.size
    vals = []
    for b in boxes:
        cx, cy, h, w = _px_box(b, W, H)
        if w < 4.0 or h < 2.0:
            return {'aspects': [], 'spread': None, 'n': 0, 'unreadable': True}
        vals.append(h / w)
    if len(vals) < 2:
        return {'aspects': [], 'spread': None, 'n': 0, 'unreadable': True}
    return {'aspects': [round(v, 4) for v in vals],
            'spread': round(max(vals) - min(vals), 4), 'n': len(vals), 'unreadable': False}

# end of aspects_code
