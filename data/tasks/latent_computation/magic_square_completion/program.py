# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: to_grid_code
def to_grid(node, n):
    """Arrange the numbers read into an n by n grid, row by row."""
    import re
    a = [str(x) for x in ((node or {}).get('answers') or [])]
    n = int(n)
    if len(a) < n * n:
        return {'rows': None, 'short': True, 'refused': True}
    m = [re.search(r'-?\d+', x) for x in a[:n * n]]
    v = [int(x.group(0)) if x else None for x in m]
    return {'rows': [v[i * n:(i + 1) * n] for i in range(n)], 'short': False}

# end of to_grid_code

# code: given_fidelity_code
def given_fidelity(read, given):
    """Share of the printed given numbers that are read back unchanged."""
    if not isinstance(read, list) or not read:
        return 0.0
    n = len(given); total = matched = 0
    for i in range(n):
        for j in range(len(given[i])):
            g = given[i][j]
            if g is None:
                continue
            total += 1
            r = read[i][j] if (i < len(read) and j < len(read[i])) else None
            if r is not None and int(r) == int(g):
                matched += 1
    return (matched / total) if total else 0.0

# end of given_fidelity_code

# code: all_lines_code
def every_line_sums(read, n, S):
    """Give 1 if every row, column and both diagonals sum to the magic total."""
    if not isinstance(read, list) or len(read) != n:
        return 0.0
    g = []
    for i in range(n):
        if not isinstance(read[i], list) or len(read[i]) != n:
            return 0.0
        row = []
        for j in range(n):
            try:
                row.append(int(read[i][j]))
            except (TypeError, ValueError):
                return 0.0
        g.append(row)
    for i in range(n):
        if sum(g[i]) != S:
            return 0.0
    for j in range(n):
        if sum(g[i][j] for i in range(n)) != S:
            return 0.0
    if sum(g[i][i] for i in range(n)) != S:
        return 0.0
    if sum(g[i][n - 1 - i] for i in range(n)) != S:
        return 0.0
    return 1.0

# end of all_lines_code

# code: blank_frac_code
def blank_fill_share(read, solution, blanks):
    """Share of the blank squares filled with the reference solution's number."""
    if not isinstance(read, list) or not read:
        return 0.0
    total = matched = 0
    for (i, j) in blanks:
        total += 1
        r = read[i][j] if (i < len(read) and j < len(read[i])) else None
        if r is not None:
            try:
                if int(r) == int(solution[i][j]):
                    matched += 1
            except (TypeError, ValueError):
                pass
    return (matched / total) if total else 0.0

# end of blank_frac_code
