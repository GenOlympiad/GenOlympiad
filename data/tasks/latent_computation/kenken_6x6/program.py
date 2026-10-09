# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: chk_code
from functools import reduce
def check_kenken_grid(grid, cages):
    """1 if the grid is a 6 by 6 Latin square and every cage meets its target, else 0."""
    n = 6
    if not isinstance(grid, list) or len(grid) != n: return 0.0
    grid_values = []
    for row in grid:
        if not isinstance(row, list) or len(row) != n: return 0.0
        row_values = []
        for v in row:
            try: row_values.append(int(v))
            except (TypeError, ValueError): return 0.0
        grid_values.append(row_values)
    for i in range(n):
        if sorted(grid_values[i]) != list(range(1, n+1)): return 0.0
        if sorted(grid_values[r][i] for r in range(n)) != list(range(1, n+1)): return 0.0
    for c in cages:
        vals = [grid_values[i][j] for (i, j) in c['cells']]
        op, t = c['op'], c['target']
        if op == '=':
            if vals[0] != t: return 0.0
        elif op == '+':
            if sum(vals) != t: return 0.0
        elif op == '*':
            if reduce(lambda x, y: x*y, vals) != t: return 0.0
        elif op == '-':
            if abs(vals[0]-vals[1]) != t: return 0.0
        elif op == '/':
            a, b = max(vals), min(vals)
            if b == 0 or a % b != 0 or a//b != t: return 0.0
    return 1.0

# end of chk_code
