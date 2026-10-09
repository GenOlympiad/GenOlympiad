# code: keys_code
def match_black_key_positions(key_boxes, reference):
    """Share of expected black key positions matched by found keys, reduced for extra keys."""
    spec = [float(s) for s in reference['spec']]
    tol = float(reference['tol'])
    boxes = list(key_boxes.get('geometry') or [])
    centres = sorted((float(b[1]) + float(b[3])) / 2000.0 for b in boxes)
    merged = []
    for c in centres:
        if merged and abs(c - merged[-1]) < 0.6 * tol:
            merged[-1] = (merged[-1] + c) / 2.0
        else:
            merged.append(c)
    centres = merged
    if len(centres) < max(2, len(spec) // 2):
        return {'frac': 0.0, 'n_found': len(centres), 'matched': 0,
                'centers': [round(c, 4) for c in centres], 'degenerate': True}
    def norm(v):
        a, b = min(v), max(v)
        return [(x - a) / (b - a) for x in v] if b > a else list(v)
    found_norm, spec_norm = norm(centres), norm(spec)
    used = [False] * len(found_norm)
    matched = 0
    for s in spec_norm:
        best, best_index = tol + 1e-9, -1
        for k, c in enumerate(found_norm):
            if used[k]:
                continue
            d = abs(c - s)
            if d < best:
                best, best_index = d, k
        if best_index >= 0 and best <= tol:
            used[best_index] = True
            matched += 1
    frac = matched / float(len(spec))
    extra = max(0, len(centres) - len(spec))
    if extra > 0:
        frac = frac * len(spec) / float(len(spec) + extra)
    return {'frac': round(frac, 4), 'matched': matched, 'n_found': len(centres),
            'centers': [round(c, 4) for c in centres], 'degenerate': False}

# end of keys_code
