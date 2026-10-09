# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_6d755312ff65
def board_cell_boxes(box, n, inset=0.15):
    """Cut the boxed board into n by n cell boxes, each shrunk by the inset."""
    geometry = (box or {}).get('geometry') or []
    if not geometry:
        return {'geometry': None, 'n': 0, 'unreadable': True}
    ymin, xmin, ymax, xmax = [float(v) for v in list(geometry[0])[:4]]
    n = int(n)
    cell_height = (ymax - ymin) / float(n)
    cell_width = (xmax - xmin) / float(n)
    out = []
    for i in range(n):
        for j in range(n):
            out.append([round(ymin + (i + inset) * cell_height, 2), round(xmin + (j + inset) * cell_width, 2),
                        round(ymin + (i + 1 - inset) * cell_height, 2), round(xmin + (j + 1 - inset) * cell_width, 2)])
    return {'geometry': out, 'n': n, 'cells': len(out), 'unreadable': False}

def cell_bit(a):
    text = str(a or '').strip()
    for ch in text:
        if ch in '01':
            return int(ch)
    low = text.lower()
    if 'black' in low:
        return 1
    if 'white' in low or 'blank' in low or 'empty' in low:
        return 0
    return None

def read_life_grid(node, n):
    """Turn the per-cell answers into a 0/1 grid, refusing when too many cells are unreadable."""
    answers = (node or {}).get('answers') or []
    n = int(n)
    if len(answers) < n * n:
        return {'grid': None, 'bad': n * n - len(answers), 'cells': len(answers), 'unreadable': True}
    grid, bad = [], 0
    for i in range(n):
        row = []
        for j in range(n):
            v = cell_bit(answers[i * n + j])
            if v is None:
                bad += 1
                v = 0
            row.append(v)
        grid.append(row)
    if bad > max(1, (n * n) // 20):
        return {'grid': None, 'bad': bad, 'cells': len(answers), 'unreadable': True}
    return {'grid': grid, 'bad': bad, 'cells': len(answers), 'unreadable': False}

def live_cell_f1(grid, target):
    """F1 overlap between the live cells read and the live cells of the reference grid."""
    live_read = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    live_target = {(r, c) for r, row in enumerate(target) for c, v in enumerate(row) if v}
    overlap = len(live_read & live_target)
    return round(2.0 * overlap / (len(live_read) + len(live_target)), 4) if (live_read or live_target) else 1.0

# end of code_6d755312ff65
