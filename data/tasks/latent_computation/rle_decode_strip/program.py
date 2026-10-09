# shared code: code_7e07f92838c6
def row_bands(grid, reference):
    """Cut the grid box into equal row bands, each slightly inset top and bottom."""
    try:
        grid_boxes = (grid or {}).get('geometry') or []
        rows = int(reference['rows'])
    except Exception:
        return {'boxes': [], 'no_read': True, 'refused': True,
                'why': 'the grid node / row count could not be read at all'}
    src = 'ring refused -> form_gate-confirmed FULL FRAME'
    y0, x0, y1, x1 = 0.0, 0.0, 1000.0, 1000.0
    if grid_boxes:
        try:
            y0, x0, y1, x1 = [float(v) for v in list(grid_boxes[0])[:4]]
            src = 'confirmed grid box'
        except Exception:
            y0, x0, y1, x1 = 0.0, 0.0, 1000.0, 1000.0
            src = 'unusable ring box -> form_gate-confirmed FULL FRAME'
    if y1 < y0: y0, y1 = y1, y0
    if x1 < x0: x0, x1 = x1, x0
    h = (y1 - y0) / float(rows) if rows else 0.0
    if rows < 2 or h <= 12.0 or (x1 - x0) <= 50.0:
        return {'boxes': [], 'no_read': True, 'refused': True,
                'why': 'grid box too small to slice (%s y %.0f..%.0f x %.0f..%.0f per-mille)'
                       % (src, y0, y1, x0, x1)}
    inset = 0.14 * h
    boxes = [[y0 + i * h + inset, x0, y0 + (i + 1) * h - inset, x1] for i in range(rows)]
    return {'boxes': [[round(v, 2) for v in b] for b in boxes], 'no_read': False,
            'why': '%s y %.0f..%.0f x %.0f..%.0f per-mille cut into %d equal row bands'
                   % (src, y0, y1, x0, x1, rows)}

# end of code_7e07f92838c6

# shared code: code_a15b98d8787c
import re
def read_row_colours(rows_ans, cols, palette):
    """Read each row's colour names, keeping the last few that fill the columns."""
    try:
        cols = int(cols)
        palette_names = [str(p).lower() for p in (palette or [])]
        reads = list((rows_ans or {}).get('answers') or [])
    except Exception:
        return {'grid': None, 'ok': False, 'read': []}
    grid = []
    for a in reads:
        toks = [w for w in re.findall(r'[a-z]+', str(a or '').lower()) if w in palette_names]
        grid.append(toks[-cols:] if len(toks) >= cols else None)
    ok = bool(grid) and all(r is not None for r in grid)
    return {'grid': grid if ok else None, 'ok': ok, 'read': [str(a) for a in reads]}

# end of code_a15b98d8787c
