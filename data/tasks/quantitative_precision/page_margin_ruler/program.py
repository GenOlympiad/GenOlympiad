# shared code: code_8ee3889ca79b
def measure_margins(sheet, block, margin, page_w_mm, page_h_mm, tol):
    """Measure the four page margins in mm and count those within tolerance."""
    sheet_box = (sheet.get('geometry') or [None])[0]
    block_box = (block.get('geometry') or [None])[0]
    if not sheet_box or not block_box:
        return {'joint': 0.0, 'n_ok': 0, 'meas': None, 'no_read': True}
    sy0, sx0, sy1, sx1 = [float(v) for v in sheet_box]
    by0, bx0, by1, bx1 = [float(v) for v in block_box]
    sh, sw = abs(sy1 - sy0), abs(sx1 - sx0)
    if sh < 20.0 or sw < 20.0:
        return {'joint': 0.0, 'n_ok': 0, 'meas': None, 'no_read': True}
    meas = {'top': (by0 - sy0) / sh * float(page_h_mm),
            'bottom': (sy1 - by1) / sh * float(page_h_mm),
            'left': (bx0 - sx0) / sw * float(page_w_mm),
            'right': (sx1 - bx1) / sw * float(page_w_mm)}
    tolerance = float(tol)
    n_ok = 0
    for k in ('top', 'bottom', 'left', 'right'):
        if abs(meas[k] - float(margin[k])) <= tolerance:
            n_ok += 1
    return {'joint': 1.0 if n_ok == 4 else 0.0, 'n_ok': n_ok,
            'meas': {k: round(meas[k], 1) for k in meas}, 'no_read': False}

# end of code_8ee3889ca79b

# code: frac4_code
def margin_share(margins):
    """The share of the four margins measured within tolerance."""
    return {'f': margins['n_ok'] / 4.0}

# end of frac4_code
