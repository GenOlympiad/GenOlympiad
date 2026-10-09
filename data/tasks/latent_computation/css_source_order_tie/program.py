# shared code: code_40ba678ebc4f
SYN = {'teal': 'cyan', 'turquoise': 'cyan', 'aqua': 'cyan', 'skyblue': 'cyan',
       'navy': 'blue', 'indigo': 'blue', 'royalblue': 'blue', 'cobalt': 'blue',
       'violet': 'purple', 'magenta': 'purple', 'lilac': 'purple', 'plum': 'purple',
       'gold': 'yellow', 'amber': 'yellow', 'mustard': 'yellow',
       'crimson': 'red', 'scarlet': 'red', 'maroon': 'red',
       'lime': 'green', 'olive': 'green', 'emerald': 'green'}
PAL = ('red', 'yellow', 'green', 'cyan', 'blue', 'purple')
def norm(a):
    w = ''
    for ch in (str(a or '').lower() + ' '):
        if ch.isalpha():
            w += ch
            continue
        t = SYN.get(w, w)
        if t in PAL:
            return t
        w = ''
    return ''
def probe_position(probe):
    """Give the probe square's row and column, counted from 1."""
    return {'row': int(probe[0]) + 1, 'col': int(probe[1]) + 1}
def crop_frame_agree(crop_read, wf):
    """Score 1 when the cut-out read matches the whole-picture read for the probe square."""
    answers = (crop_read or {}).get('answers') or []
    crop_value = norm(answers[0] if answers else '')
    frame_value = norm(wf)
    return {'frac': 1.0 if (crop_value and frame_value and crop_value == frame_value) else 0.0, 'crop': crop_value, 'frame': frame_value}

# end of code_40ba678ebc4f

# shared code: code_415fa6ac73e7
def square_boxes(tile_grid, squares, frac=0.62):
    """Shrunken boxes around the listed grid squares, with their row and column labels."""
    grid = (tile_grid or {}).get('grid')
    if not grid:
        return {'geometry': [], 'cells': [], 'unreadable': True}
    out, labels = [], []
    for rc in squares:
        r, c = int(rc[0]), int(rc[1])
        if r >= len(grid) or c >= len(grid[r]):
            return {'geometry': [], 'cells': [], 'unreadable': True}
        y0, x0, y1, x1 = grid[r][c]
        cy, cx = (y0 + y1) / 2.0, (x0 + x1) / 2.0
        hy, hx = frac * abs(y1 - y0) / 2.0, frac * abs(x1 - x0) / 2.0
        out.append([cy - hy, cx - hx, cy + hy, cx + hx])
        labels.append([r + 1, c + 1])
    return {'geometry': out, 'cells': labels, 'unreadable': False}

# end of code_415fa6ac73e7

# shared code: code_179667989edb
def order_tile_grid(tile_read, rows, cols):
    """Sort the tile boxes into a rows-by-columns grid, retrying with axes swapped."""
    def build(bx):
        n = int(rows) * int(cols)
        if not bx or len(bx) != n:
            return None
        b = [[float(v) for v in q[:4]] for q in bx]
        cen = [((q[0] + q[2]) / 2.0, (q[1] + q[3]) / 2.0, i) for i, q in enumerate(b)]
        cen.sort(key=lambda t: t[0])
        out = []
        for r in range(int(rows)):
            band = cen[r * int(cols):(r + 1) * int(cols)]
            if r:
                prev = cen[(r - 1) * int(cols):r * int(cols)]
                if max(t[0] for t in prev) >= min(t[0] for t in band):
                    return None
            band = sorted(band, key=lambda t: t[1])
            xs = [t[1] for t in band]
            if any(xs[i] >= xs[i + 1] for i in range(len(xs) - 1)):
                return None
            out.append([b[t[2]] for t in band])
        return out
    tile_boxes = (tile_read or {}).get('geometry') or []
    grid = build(tile_boxes)
    order = 'native'
    if grid is None:
        grid = build([[q[1], q[0], q[3], q[2]] for q in tile_boxes])
        order = 'axis_swapped'
    if grid is None:
        return {'grid': None, 'unreadable': True, 'frac': 0.0, 'n_boxes': len(tile_boxes),
                'order': None}
    return {'grid': grid, 'unreadable': False, 'frac': 1.0, 'n_boxes': len(tile_boxes),
            'order': order}

# end of code_179667989edb

# code: assemble_code
SYN = {'teal': 'cyan', 'turquoise': 'cyan', 'aqua': 'cyan', 'skyblue': 'cyan',
       'navy': 'blue', 'indigo': 'blue', 'royalblue': 'blue', 'cobalt': 'blue',
       'violet': 'purple', 'magenta': 'purple', 'lilac': 'purple', 'plum': 'purple',
       'gold': 'yellow', 'amber': 'yellow', 'mustard': 'yellow',
       'crimson': 'red', 'scarlet': 'red', 'maroon': 'red',
       'lime': 'green', 'olive': 'green', 'emerald': 'green'}
PAL = ('red', 'yellow', 'green', 'cyan', 'blue', 'purple')
def norm(a):
    w = ''
    for ch in (str(a or '').lower() + ' '):
        if ch.isalpha():
            w += ch
            continue
        t = SYN.get(w, w)
        if t in PAL:
            return t
        w = ''
    return ''
def assemble_row(crop_read, n_wanted):
    """Lay the read values into one grid row padded to the wanted length."""
    answers = (crop_read or {}).get('answers') or []
    row = [norm(a) for a in answers]
    row = (row + [''] * int(n_wanted))[:int(n_wanted)]
    return {'grid': [row], 'read': row, 'n_asked': len(answers)}

# end of assemble_code
