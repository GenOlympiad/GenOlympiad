# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: cells_code
def split_board_squares(board_box, n):
    """Cut the square board box into an n by n grid of inset squares."""
    n = int(n)
    b = [float(v) for v in board_box['geometry'][0]]
    y0, x0, y1, x1 = b[0], b[1], b[2], b[3]
    h, w = y1 - y0, x1 - x0
    if n < 2 or h < 150.0 or w < 150.0:
        return {'geometry': [], 'degenerate': True, 'why': 'board box too small to slice'}
    if abs(h - w) / max(h, w) > 0.25:
        return {'geometry': [], 'degenerate': True, 'why': 'board box is not square'}
    square_h, square_w = h / n, w / n
    p = 0.28
    out = []
    for r in range(n):
        for c in range(n):
            out.append([round(y0 + (r + p) * square_h, 2), round(x0 + (c + p) * square_w, 2),
                        round(y0 + (r + 1 - p) * square_h, 2), round(x0 + (c + 1 - p) * square_w, 2)])
    return {'geometry': out, 'degenerate': False, 'n': n}

# end of cells_code

# code: livef1_code
def black_square_overlap(node, n, reference_grid):
    """1 if the black squares read match the reference, else their overlap capped at 0.4."""
    n = int(n)
    answers = (node or {}).get('answers') or []
    if len(answers) != n * n:
        return {'frac': 0.0, 'no_read': True,
                'why': 'read %d cells of %d' % (len(answers), n * n)}
    vals = []
    for a in answers:
        s = str(a or '').strip().lower()
        if s.startswith('b') or 'black' in s:
            vals.append(1)
        elif s.startswith('w') or 'white' in s:
            vals.append(0)
        else:
            return {'frac': 0.0, 'no_read': True, 'why': 'a cell did not read black or white'}
    A = set()
    for i, v in enumerate(vals):
        if v:
            A.add((i // n, i % n))
    B = set()
    for r, row in enumerate(reference_grid):
        for c, v in enumerate(row):
            if v:
                B.add((r, c))
    if A == B:
        return {'frac': 1.0, 'no_read': False, 'n_black': len(A), 'exact': True}
    i = len(A & B)
    f1 = round(2.0 * i / (len(A) + len(B)), 4) if (A or B) else 1.0
    return {'frac': round(min(f1, 0.4), 4), 'no_read': False, 'n_black': len(A),
            'exact': False, 'f1': f1}

# end of livef1_code
