# shared code: code_44e83bdb16d1


def tip_alignment(tip_boxes):
    """Sideways offset and gap between the two facing tips, as fractions of the image."""
    boxes = (tip_boxes or {}).get('geometry') or []
    if len(boxes) != 2:
        return {'col_offset_frac': None, 'gap_frac': None, 'unreadable': True}
    boxes = sorted([[float(v) for v in b[:4]] for b in boxes], key=lambda b: b[0] + b[2])
    up, lo = boxes
    span = lo[2] - up[0]
    if span <= 20.0:
        return {'col_offset_frac': None, 'gap_frac': None, 'unreadable': True}
    cxu = (up[1] + up[3]) / 2.0
    cxl = (lo[1] + lo[3]) / 2.0
    return {'col_offset_frac': round(abs(cxu - cxl) / 1000.0, 4),
            'gap_frac': round(max(0.0, lo[0] - up[2]) / span, 4), 'unreadable': False,
            'span': round(span, 1)}

# end of code_44e83bdb16d1

# shared code: plumbcode

def plumb_check(res, plumb_tol, gap_target, gap_tol):
    """Score how plumb the two tips line up and how close their gap is to the target."""
    if not isinstance(res, dict) or res.get('unreadable') or res.get('col_offset_frac') is None or res.get('gap_frac') is None:
        return {'plumb': 0.0, 'gap': 0.0, 'joint': 0.0, 'no_read': True}
    def band(v, t, core, margin):
        d = abs(float(v) - float(t))
        return max(0.0, 1.0 - max(0.0, d - core) / max(margin, 1e-9))
    plumb = band(res['col_offset_frac'], 0.0, float(plumb_tol), 1.5 * float(plumb_tol))
    gap = band(res['gap_frac'], gap_target, float(gap_tol), 1.5 * float(gap_tol))
    return {'plumb': round(plumb, 4), 'gap': round(gap, 4), 'joint': round(plumb * gap, 4),
            'col_offset': res['col_offset_frac'], 'gap_frac': res['gap_frac'], 'no_read': False}

# end of plumbcode
