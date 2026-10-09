# code: split_wings_code
def split_wings(spot_boxes, spot_confirms, body_box):
    """Count confirmed eyespots left and right of the framed body, merging overlapping boxes."""
    geometry = (spot_boxes or {}).get('geometry') or []; answers = (spot_confirms or {}).get('answers') or []; body_geometry = (body_box or {}).get('geometry') or []
    if not body_geometry: return {'nl': None, 'nr': None, 'degenerate': True, 'refused': True, 'verdict': 'the body was never framed, so left and right cannot be told apart'}
    b = [float(v) for v in list(body_geometry[0])[:4]]; axis = (b[1] + b[3]) / 2.0
    cx = lambda r: (r[1] + r[3]) / 2.0; area = lambda r: max(0.0, r[2] - r[0]) * max(0.0, r[3] - r[1]); ov = lambda p, q, i, j: min(p[j], q[j]) - max(p[i], q[i])
    same = lambda p, q: ov(p, q, 0, 2) > 0 and ov(p, q, 1, 3) > 0 and min(area(p), area(q)) > 0 and ov(p, q, 0, 2) * ov(p, q, 1, 3) > 0.5 * min(area(p), area(q))
    candidates = [[float(v) for v in list(geometry[i])[:4]] for i, a in enumerate(answers) if i < len(geometry) and str(a).strip().lower().startswith('y')]
    kept = []; nl = nr = 0
    for r in candidates:
        if any(same(r, k) for k in kept): continue
        kept.append(r); nl, nr = (nl + 1, nr) if cx(r) < axis else (nl, nr + 1)
    return {'nl': nl, 'nr': nr, 'degenerate': False, 'axis': round(axis, 1), 'verdict': '%d eyespots confirmed by their own cut-outs: %d on the left of the framed body, %d on the right' % (len(kept), nl, nr)}

# end of split_wings_code
