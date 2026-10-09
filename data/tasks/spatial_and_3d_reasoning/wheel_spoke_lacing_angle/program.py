# code: lacing_code
import math


def spoke_offset_angles(reads, src):
    """Each spoke's angle away from the radial line through the hub, with their spread."""
    g = (reads or {}).get('geometry') or []
    W, H = src.size
    boxes = []
    for b in g:
        y0, x0, y1, x1 = [float(v) for v in b[:4]]
        boxes.append((min(x0, x1) * float(W) / 1000.0, min(y0, y1) * float(H) / 1000.0,
                      max(x0, x1) * float(W) / 1000.0, max(y0, y1) * float(H) / 1000.0))
    if len(boxes) < 4:
        return {'offsets': [], 'offset_spread': None, 'n': len(boxes), 'unreadable': True, 'refused': True}
    hub_x = sum((b[0] + b[2]) / 2.0 for b in boxes) / float(len(boxes))
    hub_y = sum((b[1] + b[3]) / 2.0 for b in boxes) / float(len(boxes))
    offsets = []
    for (x0, y0, x1, y1) in boxes:
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        near = min([(x0, y0), (x1, y0), (x0, y1), (x1, y1)],
                   key=lambda p: (p[0] - hub_x) ** 2 + (p[1] - hub_y) ** 2)
        far = (x0 + x1 - near[0], y0 + y1 - near[1])
        dx, dy = far[0] - near[0], far[1] - near[1]
        if math.hypot(dx, dy) < 4.0 or math.hypot(cx - hub_x, cy - hub_y) < 1.0:
            continue
        spoke = math.atan2(dy, dx)
        radial = math.atan2(cy - hub_y, cx - hub_x)
        off = abs(math.degrees(spoke - radial)) % 180.0
        offsets.append(min(off, 180.0 - off))
    if len(offsets) < 4:
        return {'offsets': [], 'offset_spread': None, 'n': len(offsets), 'unreadable': True, 'refused': True}
    return {'offsets': [round(v, 2) for v in offsets],
            'offset_spread': round(max(offsets) - min(offsets), 2),
            'mean_offset': round(sum(offsets) / float(len(offsets)), 2),
            'hub': [round(hub_x / float(W), 4), round(hub_y / float(H), 4)],
            'n': len(offsets), 'unreadable': False}

# end of lacing_code
