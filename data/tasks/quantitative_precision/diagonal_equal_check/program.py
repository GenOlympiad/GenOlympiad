# shared code: code_5c341457b56f
def select_confirmed_studs(mapped, confirms, nrect):
    """Keep the confirmed stud boxes for each frame, preferring a set of exactly four."""
    geometry = (mapped or {}).get('geometry') or []
    source_index = (mapped or {}).get('index') or []
    answers = (confirms or {}).get('answers') or []
    groups = {}
    for i, b in enumerate(geometry):
        if i >= len(source_index):
            break
        a = str(answers[i]).strip().lower() if i < len(answers) and answers[i] is not None else ''
        if not a.startswith('y'):
            continue
        groups.setdefault((source_index[i][0], int(source_index[i][1])), []).append([float(v) for v in b])
    keep, per_frame, src_used = [], [], []
    for f in range(int(nrect)):
        a4 = groups.get(('ctx', f), [])
        b4 = groups.get(('plain', f), [])
        if len(a4) == 4:
            ch, tag = a4, 'ctx'
        elif len(b4) == 4:
            ch, tag = b4, 'plain'
        elif len(a4) >= len(b4):
            ch, tag = a4, 'ctx_short'
        else:
            ch, tag = b4, 'plain_short'
        keep.extend(ch)
        per_frame.append(len(ch))
        src_used.append(tag)
    return {'boxes': keep, 'n': len(keep), 'per_frame': per_frame, 'src': src_used,
            'none': len(keep) == 0}

# end of code_5c341457b56f

# shared code: code_d2ac33d9a63f
def map_studs_to_image(frame_boxes, ctx_reads, plain_reads):
    """Map the stud boxes found inside each frame crop back to whole-image coordinates."""
    boxes = (frame_boxes or {}).get('boxes') or []
    flat, index = [], []
    for src, reads in (('ctx', ctx_reads or []), ('plain', plain_reads or [])):
        for i, r in enumerate(reads):
            if i >= len(boxes):
                break
            x0, y0, x1, y1 = boxes[i]
            for b in ((r or {}).get('geometry') or []):
                ymin, xmin, ymax, xmax = [float(v) / 1000.0 for v in b]
                flat.append([(y0 + ymin * (y1 - y0)) * 1000.0,
                             (x0 + xmin * (x1 - x0)) * 1000.0,
                             (y0 + ymax * (y1 - y0)) * 1000.0,
                             (x0 + xmax * (x1 - x0)) * 1000.0])
                index.append([src, i])
    return {'geometry': flat, 'index': index, 'n': len(flat), 'none': len(flat) == 0}

# end of code_d2ac33d9a63f

# shared code: code_966cdfdeec0d
def frame_crop_boxes(frame_reads, nrect):
    """Pad each found frame box by a tenth and order them left to right, refusing a wrong count."""
    g = (frame_reads or {}).get('geometry') or []
    K = int(nrect)
    if len(g) != K:
        return {'no_frames': True, 'n': len(g)}
    out, boxes = {}, []
    for i, b in enumerate(sorted(g, key=lambda z: (float(z[1]) + float(z[3])))):
        ymin, xmin, ymax, xmax = [float(v) / 1000.0 for v in b]
        pw, ph = (xmax - xmin) * 0.10, (ymax - ymin) * 0.10
        x0, y0 = max(0.0, xmin - pw), max(0.0, ymin - ph)
        x1, y1 = min(1.0, xmax + pw), min(1.0, ymax + ph)
        if x1 - x0 < 0.02 or y1 - y0 < 0.02:
            return {'no_frames': True, 'n': len(g)}
        out['b%d' % i] = [x0, y0, x1, y1]
        boxes.append([x0, y0, x1, y1])
    out['boxes'] = boxes
    out['no_frames'] = False
    out['n'] = len(boxes)
    return out

# end of code_966cdfdeec0d

# shared code: multidiagcode
def worst_diagonal_mismatch(centers, nrect):
    """The worst relative gap between a frame's two diagonals, 1.0 if studs are miscounted."""
    K = int(nrect)
    if centers is None or len(centers) != 4*K:
        return 1.0
    points = [(float(a), float(b)) for a, b in centers]
    points.sort(key=lambda p: p[0])
    def dist(a, b):
        return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5
    worst = 0.0
    for g in range(K):
        quad = points[g*4:(g+1)*4]
        if len(quad) != 4:
            return 1.0
        q = sorted(quad, key=lambda p: p[1])
        top = sorted(q[:2], key=lambda p: p[0])
        bot = sorted(q[2:], key=lambda p: p[0])
        TL, TR = top[0], top[1]
        BL, BR = bot[0], bot[1]
        d1 = dist(TL, BR); d2 = dist(TR, BL)
        m = (d1 + d2)/2.0
        if m <= 0:
            return 1.0
        worst = max(worst, abs(d1-d2)/m)
    return round(worst, 4)

# end of multidiagcode

# code: centers_code
def stud_centers(sel):
    """Take the centre of each kept stud box, scaling x by the median box aspect."""
    keep = (sel or {}).get('boxes') or []
    if not keep:
        return {'centers': [], 'n': 0, 'no_centers': True, 'aspect': None}
    aspects = sorted((b[2] - b[0]) / max(1e-6, (b[3] - b[1])) for b in keep)
    a = aspects[len(aspects) // 2]
    if not (0.25 <= a <= 4.0):
        a = 1.0
    points = [[(b[1] + b[3]) / 2.0 * a, (b[0] + b[2]) / 2.0] for b in keep]
    return {'centers': points, 'n': len(points), 'no_centers': False, 'aspect': round(a, 4)}

# end of centers_code
