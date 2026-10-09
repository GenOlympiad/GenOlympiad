# code: angle_set_code
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


def guyline_angle_set(reads, src):
    """Measure each red guy rope's angle and their spread, refusing if fewer than two."""
    rope_angles = _angles(reads, src)
    if not rope_angles or len(rope_angles) < 2:
        return {'angles': [], 'spread': None, 'n_segs': 0, 'unreadable': True, 'refused': True}
    return {'angles': [round(v, 2) for v in rope_angles], 'spread': round(max(rope_angles) - min(rope_angles), 2),
            'n_segs': len(rope_angles), 'unreadable': False}

# end of angle_set_code
