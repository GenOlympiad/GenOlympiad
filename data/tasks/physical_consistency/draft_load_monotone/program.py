# code: draftfrac_code

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


def freeboards(bx, image, n_want):
    geo = (bx or {}).get('geometry') or []
    k = int(n_want)
    if len(geo) != k:
        return {'h': None, 'degenerate': True, 'n': len(geo)}
    W, H = width_height(image) if isinstance(image, str) else (1.0, 1.0)
    bs = []
    for g in geo:
        y0, x0, y1, x1 = [float(v) for v in list(g)[:4]]
        bs.append((0.5 * (x0 + x1) * W / 1000.0, y0 * H / 1000.0, y1 * H / 1000.0))
    bs.sort(key=lambda b: b[0])
    bots = sorted(b[2] for b in bs)
    m = len(bots)
    base = bots[m // 2] if m % 2 else 0.5 * (bots[m // 2 - 1] + bots[m // 2])
    hs = [base - b[1] for b in bs]
    tall = max(hs)
    if tall <= 0:
        return {'h': None, 'degenerate': True, 'n': len(geo)}
    return {'h': [round(x / tall, 4) for x in hs], 'degenerate': False, 'n': len(geo)}


def order_frac(d, loads):
    if not isinstance(d, dict) or d.get('h') is None:
        return 0.0
    h = d['h']
    L = [float(x) for x in loads]
    if len(h) != len(L):
        return 0.0
    good = tot = 0
    for i in range(len(h)):
        for j in range(i + 1, len(h)):
            if L[i] == L[j]:
                continue
            tot += 1
            want_lower_i = L[i] > L[j]
            got_lower_i = h[i] < h[j] - 0.02
            got_lower_j = h[j] < h[i] - 0.02
            if want_lower_i and got_lower_i:
                good += 1
            elif (not want_lower_i) and got_lower_j:
                good += 1
    if tot == 0:
        return 0.0
    f = good / float(tot)
    return 1.0 if f > 0.999 else (round(f * 0.6, 4) if f >= 0.5 else 0.0)


def draft_order_score(boxes, image, k, loads):
    """Score how well the float freeboards order the floats by load, 0 if boxes are unusable."""
    found = freeboards(boxes, image, k)
    if found.get('degenerate'):
        return {'frac': 0.0, 'degenerate': True, 'found_boxes': found}
    return {'frac': order_frac(found, loads), 'degenerate': False, 'found_boxes': found}

# end of draftfrac_code

# code: m_code
def heaviest_float_picked(idx, loads):
    """Score 1 if the float number read carries the largest load."""
    try:
        i = int(round(float(idx))) - 1
    except (TypeError, ValueError):
        return 0.0
    load_values = [float(x) for x in loads]
    if i < 0 or i >= len(load_values):
        return 0.0
    return 1.0 if load_values[i] == max(load_values) else 0.0

# end of m_code
