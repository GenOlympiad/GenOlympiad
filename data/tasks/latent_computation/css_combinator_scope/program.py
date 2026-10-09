# shared code: code_3c58b63e3e61
SYN = {'teal': 'cyan', 'turquoise': 'cyan', 'aqua': 'cyan', 'skyblue': 'cyan',
       'navy': 'blue', 'indigo': 'blue', 'royalblue': 'blue',
       'violet': 'purple', 'magenta': 'purple', 'lilac': 'purple', 'plum': 'purple',
       'gold': 'yellow', 'amber': 'yellow', 'mustard': 'yellow',
       'crimson': 'red', 'scarlet': 'red', 'maroon': 'red',
       'lime': 'green', 'olive': 'green', 'emerald': 'green'}
def colour_name(s):
    """Lower case the colour word and map it through the synonym table."""
    w = ''.join(ch for ch in str(s).lower() if ch.isalpha())
    return SYN.get(w, w)
def probe_square_colour(grid, position, rows, cols):
    """The normalised colour read at one tile, with a box for drawing it."""
    r, c = position
    box = [(c + 0.5) / cols, (r + 0.5) / rows, 0.56 / cols, 0.56 / rows]
    got = grid[r][c] if (grid and r < len(grid) and c < len(grid[r])) else 'none'
    return {'rect': [box], 'color': colour_name(got)}

# end of code_3c58b63e3e61

# shared code: code_4f07e53dcd5d

import re

SYN = {'teal': 'cyan', 'turquoise': 'cyan', 'aqua': 'cyan', 'skyblue': 'cyan',
       'navy': 'blue', 'indigo': 'blue', 'royalblue': 'blue',
       'violet': 'purple', 'magenta': 'purple', 'lilac': 'purple', 'plum': 'purple',
       'gold': 'yellow', 'amber': 'yellow', 'mustard': 'yellow',
       'crimson': 'red', 'scarlet': 'red', 'maroon': 'red',
       'lime': 'green', 'olive': 'green', 'emerald': 'green'}


def _words(a, want, pal):
    out = []
    for w in re.findall(r'[a-z]+', str(a or '').lower()):
        w = SYN.get(w, w)
        if w in pal:
            out.append(w)
    return out if len(out) == want else None


def assemble_colour_grid(reads, plan, rows, cols, palette):
    """Join the colours read from each strip into a full grid, marking unread tiles."""
    rows, cols = int(rows), int(cols)
    palette_words = [str(p).lower() for p in (palette or [])]
    if not isinstance(plan, dict) or plan.get('no_plan'):
        return {'no_read': True, 'grid': None, 'reason': 'the board was never boxed'}
    m, per_row = int(plan['m']), int(plan['per_row'])
    answers = (reads.get('answers') if isinstance(reads, dict) else reads) or []
    grid, n_missing = [], 0
    for i in range(rows):
        row = []
        for c in range(per_row):
            k = i * per_row + c
            piece = _words(answers[k] if k < len(answers) else None, m, palette_words)
            if piece is None:
                n_missing += 1
                piece = ['?'] * m
            row += piece
        grid.append(row)
    if n_missing >= rows * per_row:
        return {'no_read': True, 'grid': None, 'n_missing': n_missing,
                'reason': 'every strip of the board refused to read'}
    return {'no_read': False, 'grid': grid, 'n_missing': n_missing,
            'n_cells_read': sum(1 for r in grid for v in r if v != '?'),
            'n_cells': rows * cols}

# end of code_4f07e53dcd5d

# shared code: code_1a324c29b1c4

def plan_board_strips(image, b1, b2, b3, rows, cols):
    """Choose the board box closest to the expected aspect and cut it into row strips."""
    import math
    import struct

    def _wh(p):
        try:
            with open(str(p), 'rb') as f:
                head = f.read(2048)
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

    rows, cols = int(rows), int(cols)
    size = _wh(image)
    W, H = size if size else (1000.0, 1000.0)
    expected_aspect = float(cols) / float(rows)
    live, candidates = [], []
    for tag, b in (('A', b1), ('B', b2), ('C', b3)):
        gm = b.get('geometry') if isinstance(b, dict) else b
        if not gm:
            candidates.append({'tag': tag, 'box': None, 'why': 'the reader refused this wording'})
            continue
        y0, x0, y1, x1 = [float(v) for v in gm[0][:4]]
        if x1 - x0 < 50 or y1 - y0 < 50:
            candidates.append({'tag': tag, 'box': [y0, x0, y1, x1], 'why': 'degenerate box'})
            continue
        asp = ((x1 - x0) * W) / max(1e-6, (y1 - y0) * H)
        d = abs(math.log(asp / expected_aspect))
        candidates.append({'tag': tag, 'box': [round(y0), round(x0), round(y1), round(x1)],
                      'aspect': round(asp, 3), 'log_dev': round(d, 3),
                      'area': round((x1 - x0) * (y1 - y0))})
        live.append((d, (x1 - x0) * (y1 - y0), tag, (y0, x0, y1, x1)))
    best, bestd = None, None
    if live:
        bestd = min(r[0] for r in live)
        near = [r for r in live if r[0] <= bestd + 0.05]
        near.sort(key=lambda r: r[1])
        best = near[0][3]
        for c in candidates:
            if c.get('tag') == near[0][2]:
                c['chosen'] = True
    if best is None or bestd > 0.35:
        return {'no_plan': True, 'expected_aspect': round(expected_aspect, 3), 'candidates': candidates,
                'reason': ('none of the three board proposals has the %d:%d aspect the '
                           'stylesheet pins (best off by %sx)'
                           % (cols, rows, round(math.exp(bestd), 2) if bestd else None))}
    y0, x0, y1, x1 = best
    m = 1
    for k in range(2, 6):
        if cols % k == 0:
            m = k
    rects = [[(j + 0.5) / cols, (i + 0.5) / rows, 0.86 / cols, 0.86 / rows]
             for i in range(rows) for j in range(cols)]
    chunks = []
    for i in range(rows):
        ry0 = y0 + (y1 - y0) * i / float(rows)
        ry1 = y0 + (y1 - y0) * (i + 1) / float(rows)
        for j in range(0, cols, m):
            chunks.append([ry0, x0 + (x1 - x0) * j / float(cols),
                           ry1, x0 + (x1 - x0) * (j + m) / float(cols)])
    return {'no_plan': False, 'rects': rects, 'm': m, 'per_row': cols // m,
            'expected_aspect': round(expected_aspect, 3), 'candidates': candidates,
            'chosen': [round(y0), round(x0), round(y1), round(x1)],
            'found_anchors': [[x0 * W / 1000.0, y0 * H / 1000.0],
                            [x1 * W / 1000.0, y0 * H / 1000.0],
                            [x1 * W / 1000.0, y1 * H / 1000.0],
                            [x0 * W / 1000.0, y1 * H / 1000.0]],
            'chunks': {'geometry': chunks}, 'frame': [W, H]}

# end of code_1a324c29b1c4

# code: pick_code
def colours_at_squares(grid, positions):
    """The colours read at the contested tile positions, as one row."""
    if not grid:
        return [[]]
    return [[grid[r][c] for r, c in positions]]

# end of pick_code

# code: verdict_code
def compare_grid(grid, reference_grid, rows, cols):
    """Split the tiles into right and wrong boxes against the reference grid."""
    ok, bad = [], []
    for r in range(rows):
        for c in range(cols):
            box = [(c + 0.5) / cols, (r + 0.5) / rows,
                   0.70 / cols, 0.70 / rows]
            got = grid[r][c] if (grid and r < len(grid) and c < len(grid[r])) else None
            (ok if str(got) == str(reference_grid[r][c]) else bad).append(box)
    return {'ok': ok, 'bad': bad, 'n_bad': len(bad), 'n_ok': len(ok),
            'all_ok': ('yes' if not bad else 'no')}

# end of verdict_code
