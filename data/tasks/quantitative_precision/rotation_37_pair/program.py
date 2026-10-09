# shared code: rotcode
def rotation_error(centers, target_deg):
    """How far the mean turn between the two dot triangles is from the target angle."""
    if centers is None or len(centers) != 6:
        return 90.0
    points = [(float(a), float(b)) for a, b in centers]
    points.sort(key=lambda p: p[1])
    A = points[:3]; B = points[3:]
    def centroid(S):
        return (sum(p[0] for p in S)/len(S), sum(p[1] for p in S)/len(S))
    ca, cb = centroid(A), centroid(B)
    import math as _m
    def by_angle(S, c):
        return sorted(S, key=lambda p: _m.atan2(p[1]-c[1], p[0]-c[0]))
    A = by_angle(A, ca); B = by_angle(B, cb)
    angles = []
    for (ax, ay), (bx, by) in zip(A, B):
        va = _m.atan2(ay-ca[1], ax-ca[0])
        vb = _m.atan2(by-cb[1], bx-cb[0])
        turn = _m.degrees(vb - va)
        turn = (turn + 180) % 360 - 180
        angles.append(abs(turn))
    measured = sum(angles)/len(angles)
    return round(abs(measured - float(target_deg)), 4)

# end of rotcode

# code: n_dots_code
import re
def count_confirmed_dots(confirm_reads):
    """Count the dots confirmed by a yes answer."""
    answers = (confirm_reads or {}).get('answers') or []
    return sum(1 for a in answers if re.match(r'\s*y', str(a or ''), re.I))

# end of n_dots_code

# code: dot_centers_code
def dot_centers(dots, im):
    """Pixel centres of the boxed dots."""
    dot_boxes = (dots or {}).get('geometry') or []
    try:
        W, H = im.size
    except Exception:
        W, H = 1000.0, 1000.0
    centres = []
    for b in dot_boxes:
        y0, x0, y1, x1 = [float(v) for v in b[:4]]
        centres.append([((x0 + x1) / 2.0) * float(W) / 1000.0,
                    ((y0 + y1) / 2.0) * float(H) / 1000.0])
    return {'centers': centres, 'n': len(centres), 'size': [float(W), float(H)]}

# end of dot_centers_code
