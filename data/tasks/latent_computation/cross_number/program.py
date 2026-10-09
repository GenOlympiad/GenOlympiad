# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: clues_hold_code
def clues_hold(grid):
    """Check that the read 3 by 3 digit grid satisfies every across and down clue."""
    values = grid.get('values') if isinstance(grid, dict) else grid
    try:
        cells = [[int(str(c).strip()) for c in row] for row in (values or [])]
    except (TypeError, ValueError):
        return 'malformed'
    if len(cells) != 3 or any(len(r) != 3 for r in cells):
        return 'malformed'
    if any(c < 0 or c > 9 for row in cells for c in row):
        return 'malformed'
    def num(digs):
        return digs[0] * 100 + digs[1] * 10 + digs[2]
    def prime(n):
        if n < 2:
            return False
        k = 2
        while k * k <= n:
            if n % k == 0:
                return False
            k += 1
        return True
    rows = [num(r) for r in cells]
    colsd = [[cells[i][j] for i in range(3)] for j in range(3)]
    cols = [num(c) for c in colsd]
    lead_ok = all(r[0] != 0 for r in cells) and all(c[0] != 0 for c in colsd)
    ok = (lead_ok and prime(rows[0]) and rows[1] % 111 == 0
          and str(rows[2]) == str(rows[2])[::-1] and cols[0] % 9 == 0
          and prime(cols[2]) and cols[1] == rows[0] - rows[2])
    return 'holds' if ok else 'violated'

# end of clues_hold_code
