# shared code: code_37304e2ca189
def confirmed_hole_points(hole_confirms, holes):
    """The expected hole positions the judge VLM confirmed as punched."""
    ans = (hole_confirms or {}).get('answers') or []
    points = [[float(h[0]), float(h[1])] for i, h in enumerate(holes or [])
           if i < len(ans) and str(ans[i]).strip().lower().startswith('y')]
    return {'points': points, 'n': len(points), 'no_read': len(points) == 0}

# end of code_37304e2ca189

# shared code: code_186a2b1a42df
def plan_hole_boxes(image, sheet, holes):
    """A crop box around each expected hole position on the boxed sheet, with the overlay circles."""
    import struct

    def width_height(p):
        try:
            with open(str(p), 'rb') as f:
                head = f.read(4096)
        except Exception:
            return None
        if head[:8] == b'\x89PNG\r\n\x1a\n':
            w, h = struct.unpack('>II', head[16:24])
            return float(w), float(h)
        if head[:2] == b'\xff\xd8':
            i = 2
            while i + 9 < len(head):
                if head[i] != 0xFF:
                    break
                mk = head[i + 1]
                ln = struct.unpack('>H', head[i + 2:i + 4])[0]
                if 0xC0 <= mk <= 0xCF and mk not in (0xC4, 0xC8, 0xCC):
                    h, w = struct.unpack('>HH', head[i + 5:i + 9])
                    return float(w), float(h)
                i += 2 + ln
        return None

    sheet_box = ((sheet or {}).get('geometry') or [None])[0]
    points = [[float(h[0]), float(h[1])] for h in (holes or [])]
    if not sheet_box or not points:
        return {'no_plan': True}
    sy0, sx0, sy1, sx1 = [float(v) for v in sheet_box]
    if abs(sy1 - sy0) < 80.0 or abs(sx1 - sx0) < 80.0:
        return {'no_plan': True}
    size = width_height(image)
    if not size:
        return {'no_plan': True}
    W, H = size
    x0, x1 = min(sx0, sx1) * W / 1000.0, max(sx0, sx1) * W / 1000.0
    y0, y1 = min(sy0, sy1) * H / 1000.0, max(sy0, sy1) * H / 1000.0
    sheet_width, sheet_height = x1 - x0, y1 - y0
    half = 0.075 * min(sheet_width, sheet_height)
    boxes = []
    for u, v in points:
        cx, cy = x0 + u * sheet_width, y0 + v * sheet_height
        boxes.append([max(0.0, (cy - half)) * 1000.0 / H, max(0.0, (cx - half)) * 1000.0 / W,
                      min(H, (cy + half)) * 1000.0 / H, min(W, (cx + half)) * 1000.0 / W])
    return {'no_plan': False, 'W': W, 'H': H,
            'circles': [[u, v, 0.12] for u, v in points],
            'found_anchors': [[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
            'boxes': boxes}

# end of code_186a2b1a42df

# code: tally_code
def count_holes(hole_confirms, extra_answer):
    """The number of confirmed holes, plus one if an extra hole was seen."""
    ans = (hole_confirms or {}).get('answers') or []
    n = sum(1 for a in ans if str(a).strip().lower().startswith('y'))
    extra = str(extra_answer).strip().lower().startswith('y')
    return {'n': n + (1 if extra else 0), 'matched': n, 'extra': extra, 'asked': len(ans)}

# end of tally_code
