# shared code: code_17900659001e
def read_grid(hole_reads, rows, cols):
    """Turn the yes or no hole answers into a grid of 1s and 0s."""
    rows, cols = int(rows), int(cols)
    answers = (hole_reads or {}).get('answers') or []
    if len(answers) != rows * cols:
        return {'grid': None, 'ok': False, 'read': answers}
    bits = []
    for a in answers:
        s = str(a or '').strip().lower()
        if s.startswith('y'):
            bits.append(1)
        elif s.startswith('n'):
            bits.append(0)
        else:
            return {'grid': None, 'ok': False, 'read': answers}
    return {'grid': [bits[i * cols:(i + 1) * cols] for i in range(rows)],
            'ok': True, 'read': answers}

# end of code_17900659001e

# shared code: code_12495814c3c5
def grid_square_boxes(card, rows, cols):
    """Inset boxes for each grid square, from the confirmed grid box."""
    rows, cols = int(rows), int(cols)
    if rows <= 0 or cols <= 0:
        return {'boxes': None, 'rows': rows, 'cols': cols, 'anchor': 'none'}
    grid_geometry = (card or {}).get('geometry') or []
    if grid_geometry:
        y0, x0, y1, x1 = [float(v) for v in grid_geometry[0][:4]]
        anchor = 'confirmed grid box'
    else:
        y0, x0, y1, x1 = 0.0, 0.0, 1000.0, 1000.0
        anchor = 'full frame (ring refused; prompt pins the grid edge-to-edge)'
    if y1 - y0 < 100.0 or x1 - x0 < 100.0:
        y0, x0, y1, x1 = 0.0, 0.0, 1000.0, 1000.0
        anchor = 'full frame (degenerate box)'
    inset = 0.12
    h = (y1 - y0) / float(rows)
    w = (x1 - x0) / float(cols)
    out = []
    for i in range(rows):
        for j in range(cols):
            out.append([y0 + h * i + h * inset, x0 + w * j + w * inset,
                        y0 + h * (i + 1) - h * inset, x0 + w * (j + 1) - w * inset])
    return {'boxes': out, 'rows': rows, 'cols': cols, 'n': len(out),
            'inset': inset, 'anchor': anchor, 'rect': [y0, x0, y1, x1]}

# end of code_12495814c3c5

# code: parity_code
def even_parity(grid_read):
    """1 if every row and column of the 8 by 8 grid holds an even number of holes."""
    grid = (grid_read or {}).get('grid')
    if not grid or len(grid) != 8 or any(len(r) != 8 for r in grid):
        return {'frac': 0.0, 'why': 'the 8x8 punch grid did not transcribe'}
    for r in range(8):
        if sum(grid[r]) % 2 != 0:
            return {'frac': 0.0, 'why': 'row %d holds an ODD number of holes (%d)'
                    % (r + 1, sum(grid[r]))}
    for c in range(8):
        s = sum(grid[r][c] for r in range(8))
        if s % 2 != 0:
            return {'frac': 0.0, 'why': 'column %d holds an ODD number of holes (%d)'
                    % (c + 1, s)}
    return {'frac': 1.0, 'why': 'all 8 rows and all 8 columns hold an even number of holes'}

# end of parity_code

# code: exact_code
def grid_matches(grid_read, want):
    """1 if the transcribed 8 by 8 grid equals the specified pattern."""
    grid = (grid_read or {}).get('grid')
    if not grid or len(grid) != 8 or any(len(r) != 8 for r in grid):
        return {'frac': 0.0, 'why': 'the 8x8 punch grid did not transcribe'}
    same = [list(r) for r in grid] == [list(r) for r in want]
    n_differ = sum(1 for i in range(8) for j in range(8) if grid[i][j] != want[i][j])
    return {'frac': 1.0 if same else 0.0,
            'why': '%d of 64 cells differ from the specified pattern' % n_differ}

# end of exact_code

# code: hole_count_code
def hole_count(grid_read):
    """Count the punched holes in the transcribed grid."""
    grid = (grid_read or {}).get('grid')
    if not grid:
        return None
    return sum(1 for row in grid for value in row if int(value) == 1)

# end of hole_count_code
