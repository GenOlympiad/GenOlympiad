# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

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
    """The probed tile's row and column, counted from 1."""
    return {'row': int(probe[0]) + 1, 'col': int(probe[1]) + 1}
def crop_frame_agree(cr, wf):
    a = (cr or {}).get('answers') or []
    c = norm(a[0] if a else '')
    f = norm(wf)
    return {'frac': 1.0 if (c and f and c == f) else 0.0, 'crop': c, 'frame': f}

# end of code_40ba678ebc4f

# shared code: code_415fa6ac73e7
def square_boxes(lat, idx, frac=0.62):
    g = (lat or {}).get('grid')
    if not g:
        return {'geometry': [], 'cells': [], 'unreadable': True}
    out, tags = [], []
    for rc in idx:
        r, c = int(rc[0]), int(rc[1])
        if r >= len(g) or c >= len(g[r]):
            return {'geometry': [], 'cells': [], 'unreadable': True}
        y0, x0, y1, x1 = g[r][c]
        cy, cx = (y0 + y1) / 2.0, (x0 + x1) / 2.0
        hy, hx = frac * abs(y1 - y0) / 2.0, frac * abs(x1 - x0) / 2.0
        out.append([cy - hy, cx - hx, cy + hy, cx + hx])
        tags.append([r + 1, c + 1])
    return {'geometry': out, 'cells': tags, 'unreadable': False}

# end of code_415fa6ac73e7

# shared code: code_179667989edb
def order_tile_grid(tiles, rows, cols):
    """Sort the framed tiles into a rows by columns grid, trying swapped axes if needed."""
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
    raw = (tiles or {}).get('geometry') or []
    grid = build(raw)
    order = 'native'
    if grid is None:
        grid = build([[q[1], q[0], q[3], q[2]] for q in raw])
        order = 'axis_swapped'
    if grid is None:
        return {'grid': None, 'unreadable': True, 'frac': 0.0, 'n_boxes': len(raw),
                'order': None}
    return {'grid': grid, 'unreadable': False, 'frac': 1.0, 'n_boxes': len(raw),
            'order': order}

# end of code_179667989edb

# code: shortfall_for_cascade_code

import re
def _first_int(node):
    hits = [m for m in [re.findall(r'\d+', str(a if a is not None else '')) for a in ((node or {}).get('answers') or [])] if m]
    return int(hits[0][0]) if hits else None
def shortfall_for_cascade(tiles, count_read, lat, rows, cols):
    """Whether the boxed tile count and a separate count both say the page is short of tiles."""
    want = int(rows) * int(cols); n_box = len((tiles or {}).get('geometry') or []); count_said = _first_int(count_read)
    if not (lat or {}).get('unreadable'): return {'unreadable': False, 'short': False, 'n_boxes': n_box, 'n_said': count_said, 'verdict': 'the %d framed tiles form the %dx%d lattice the page promised' % (n_box, int(rows), int(cols))}
    if count_said is None: return {'unreadable': True, 'refused': True, 'short': False, 'n_boxes': n_box, 'n_said': None, 'verdict': 'no lattice, and the second reader gave no number -> held'}
    if n_box != want and count_said != want: return {'unreadable': False, 'short': True, 'n_boxes': n_box, 'n_said': count_said, 'verdict': 'two independent readings agree the page is short: the certified box count framed %d tiles and a separate count read %d, against the %d tiles the page was told to print' % (n_box, count_said, want)}
    return {'unreadable': True, 'refused': True, 'short': False, 'n_boxes': n_box, 'n_said': count_said, 'verdict': 'the two readings disagree (boxes %d, count %d, promised %d) -> held' % (n_box, count_said, want)}

# end of shortfall_for_cascade_code

# code: cells_for_contested_code

def boxes_for_contested(lat, idx, short, frac=0.62):
    """Shrunk boxes for the contested grid squares, or a placeholder when the page is short."""
    if (short or {}).get('short'): return {'geometry': [[400, 400, 600, 600]], 'cells': [[0, 0]], 'unreadable': False, 'short': True}
    grid = (lat or {}).get('grid')
    if not grid: return {'geometry': [], 'cells': [], 'unreadable': True, 'refused': True, 'short': False}
    out, positions = [], []
    for row_col in idx:
        r, c = int(row_col[0]), int(row_col[1])
        if r >= len(grid) or c >= len(grid[r]): return {'geometry': [], 'cells': [], 'unreadable': True, 'refused': True, 'short': False}
        y0, x0, y1, x1 = grid[r][c]
        cy, cx = (y0 + y1) / 2.0, (x0 + x1) / 2.0; hy, hx = frac * abs(y1 - y0) / 2.0, frac * abs(x1 - x0) / 2.0
        out.append([cy - hy, cx - hx, cy + hy, cx + hx]); positions.append([r + 1, c + 1])
    return {'geometry': out, 'cells': positions, 'unreadable': False, 'short': False}

# end of cells_for_contested_code

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
def colour_row(cr, want, short):
    """The colour word read for each contested tile, padded to the expected count."""
    if (short or {}).get('short'):
        return {'grid': [[''] * int(want)], 'read': [], 'n_asked': 0,
                'short': True, 'verdict': (short or {}).get('verdict')}
    answers = (cr or {}).get('answers') or []
    row = [norm(a) for a in answers]
    row = (row + [''] * int(want))[:int(want)]
    return {'grid': [row], 'read': row, 'n_asked': len(answers), 'short': False}

# end of assemble_code

# code: shortfall_for_lattice_code

import re
def _first_int(node):
    hits = [m for m in [re.findall(r'\d+', str(a if a is not None else '')) for a in ((node or {}).get('answers') or [])] if m]
    return int(hits[0][0]) if hits else None
def shortfall_for_lattice(tiles, count_read, lat, rows, cols):
    """Whether the boxed tile count and a separate count both say the page is short of tiles."""
    want = int(rows) * int(cols); n_box = len((tiles or {}).get('geometry') or []); count_said = _first_int(count_read)
    if not (lat or {}).get('unreadable'): return {'unreadable': False, 'short': False, 'n_boxes': n_box, 'n_said': count_said, 'verdict': 'the %d framed tiles form the %dx%d lattice the page promised' % (n_box, int(rows), int(cols))}
    if count_said is None: return {'unreadable': True, 'refused': True, 'short': False, 'n_boxes': n_box, 'n_said': None, 'verdict': 'no lattice, and the second reader gave no number -> held'}
    if n_box != want and count_said != want: return {'unreadable': False, 'short': True, 'n_boxes': n_box, 'n_said': count_said, 'verdict': 'two independent readings agree the page is short: the certified box count framed %d tiles and a separate count read %d, against the %d tiles the page was told to print' % (n_box, count_said, want)}
    return {'unreadable': True, 'refused': True, 'short': False, 'n_boxes': n_box, 'n_said': count_said, 'verdict': 'the two readings disagree (boxes %d, count %d, promised %d) -> held' % (n_box, count_said, want)}

# end of shortfall_for_lattice_code

# code: shortfall_for_probe_code

import re
def _first_int(node):
    hits = [m for m in [re.findall(r'\d+', str(a if a is not None else '')) for a in ((node or {}).get('answers') or [])] if m]
    return int(hits[0][0]) if hits else None
def shortfall_for_probe(tiles, count_read, lat, rows, cols):
    """Whether the boxed tile count and a separate count both say the page is short of tiles."""
    want = int(rows) * int(cols); n_box = len((tiles or {}).get('geometry') or []); count_said = _first_int(count_read)
    if not (lat or {}).get('unreadable'): return {'unreadable': False, 'short': False, 'n_boxes': n_box, 'n_said': count_said, 'verdict': 'the %d framed tiles form the %dx%d lattice the page promised' % (n_box, int(rows), int(cols))}
    if count_said is None: return {'unreadable': True, 'refused': True, 'short': False, 'n_boxes': n_box, 'n_said': None, 'verdict': 'no lattice, and the second reader gave no number -> held'}
    if n_box != want and count_said != want: return {'unreadable': False, 'short': True, 'n_boxes': n_box, 'n_said': count_said, 'verdict': 'two independent readings agree the page is short: the certified box count framed %d tiles and a separate count read %d, against the %d tiles the page was told to print' % (n_box, count_said, want)}
    return {'unreadable': True, 'refused': True, 'short': False, 'n_boxes': n_box, 'n_said': count_said, 'verdict': 'the two readings disagree (boxes %d, count %d, promised %d) -> held' % (n_box, count_said, want)}

# end of shortfall_for_probe_code

# code: cells_for_probe_code

def boxes_for_probe(lat, idx, short, frac=0.62):
    """A shrunk box for the probed grid square, or a placeholder when the page is short."""
    if (short or {}).get('short'): return {'geometry': [[400, 400, 600, 600]], 'cells': [[0, 0]], 'unreadable': False, 'short': True}
    grid = (lat or {}).get('grid')
    if not grid: return {'geometry': [], 'cells': [], 'unreadable': True, 'refused': True, 'short': False}
    out, positions = [], []
    for row_col in idx:
        r, c = int(row_col[0]), int(row_col[1])
        if r >= len(grid) or c >= len(grid[r]): return {'geometry': [], 'cells': [], 'unreadable': True, 'refused': True, 'short': False}
        y0, x0, y1, x1 = grid[r][c]
        cy, cx = (y0 + y1) / 2.0, (x0 + x1) / 2.0; hy, hx = frac * abs(y1 - y0) / 2.0, frac * abs(x1 - x0) / 2.0
        out.append([cy - hy, cx - hx, cy + hy, cx + hx]); positions.append([r + 1, c + 1])
    return {'geometry': out, 'cells': positions, 'unreadable': False, 'short': False}

# end of cells_for_probe_code

# code: agree_code

SYN = {'teal': 'cyan', 'turquoise': 'cyan', 'aqua': 'cyan', 'skyblue': 'cyan', 'navy': 'blue', 'indigo': 'blue', 'royalblue': 'blue', 'cobalt': 'blue', 'violet': 'purple', 'magenta': 'purple', 'lilac': 'purple', 'plum': 'purple', 'gold': 'yellow', 'amber': 'yellow', 'mustard': 'yellow', 'crimson': 'red', 'scarlet': 'red', 'maroon': 'red', 'lime': 'green', 'olive': 'green', 'emerald': 'green'}
PAL = ('red', 'yellow', 'green', 'cyan', 'blue', 'purple')
def norm(a):
    ws = [SYN.get(w, w) for w in ''.join(c if c.isalpha() else ' ' for c in str(a or '').lower()).split()]; hits = [w for w in ws if w in PAL]
    return hits[0] if hits else ''
def colours_agree(crop_read, frame_read, short):
    """Score 1 when the tile cut-out and the whole-frame read name the same colour."""
    if (short or {}).get('short'): return {'frac': 0.0, 'crop': '', 'frame': '', 'short': True, 'verdict': (short or {}).get('verdict')}
    answers = (crop_read or {}).get('answers') or []; crop_colour = norm(answers[0] if answers else ''); frame_colour = norm(frame_read)
    return {'frac': 1.0 if (crop_colour and frame_colour and crop_colour == frame_colour) else 0.0, 'crop': crop_colour, 'frame': frame_colour, 'short': False}

# end of agree_code
