# shared code: code_efcc7c2efe2c
def assemble_board(line_reads):
    """Build the 15 by 15 board from the stone strings read per line, flagging misreads."""
    import re
    answers = (line_reads or {}).get('answers') or []
    grid, bad = [], False
    for a in answers:
        runs = re.findall(r'[BW.]{5,}', str(a or '').upper())
        token = max(runs, key=len) if runs else ''
        if len(token) != 15:
            bad = True
            token = (token + '.' * 15)[:15]
        grid.append(token)
    if len(grid) != 15:
        bad = True
        grid = (grid + ['.' * 15] * 15)[:15]
    return {'grid': grid, 'bad': bad}

# end of code_efcc7c2efe2c

# shared code: code_bcaede986f1d
def line_strip_boxes(board_box):
    """Cut the board box into 15 horizontal strips, one per board line."""
    b = [float(v) for v in board_box['geometry'][0]]
    ymin, xmin, ymax, xmax = b[0], b[1], b[2], b[3]
    sy = ymax - ymin
    sx = xmax - xmin
    if sy < 200.0 or sx < 200.0:
        return {'boxes': [], 'bad': True}
    pitch = sy / 14.0
    half = pitch * 0.7
    padx = sx / 14.0 * 0.45
    out = []
    for i in range(15):
        cy = ymin + i * pitch
        out.append([max(0.0, cy - half), max(0.0, xmin - padx),
                    min(1000.0, cy + half), min(1000.0, xmax + padx)])
    return {'boxes': out, 'bad': False, 'pitch': round(pitch, 2)}

# end of code_bcaede986f1d

# code: gate_code
def gomoku_props(grid):
    n = len(grid)
    DIRS = ((0, 1), (1, 0), (1, 1), (1, -1))

    def run_len(g, r, c, dr, dc):
        who = g[r][c]
        if who == '.':
            return 0
        length = 1
        rr, cc = r + dr, c + dc
        while 0 <= rr < n and 0 <= cc < len(g[rr]) and g[rr][cc] == who:
            length += 1
            rr += dr
            cc += dc
        rr, cc = r - dr, c - dc
        while 0 <= rr < n and 0 <= cc < len(g[rr]) and g[rr][cc] == who:
            length += 1
            rr -= dr
            cc -= dc
        return length

    def has_five(g, who):
        for r in range(n):
            for c in range(len(g[r])):
                if g[r][c] != who:
                    continue
                for dr, dc in DIRS:
                    if run_len(g, r, c, dr, dc) >= 5:
                        return True
        return False

    def makes_five_for_black(g, r, c):
        for dr, dc in DIRS:
            length = 1
            rr, cc = r + dr, c + dc
            while 0 <= rr < n and 0 <= cc < len(g[rr]) and g[rr][cc] == 'B':
                length += 1
                rr += dr
                cc += dc
            rr, cc = r - dr, c - dc
            while 0 <= rr < n and 0 <= cc < len(g[rr]) and g[rr][cc] == 'B':
                length += 1
                rr -= dr
                cc -= dc
            if length >= 5:
                return True
        return False

    n_black = sum(row.count('B') for row in grid)
    n_white = sum(row.count('W') for row in grid)
    five_black = has_five(grid, 'B')
    five_white = has_five(grid, 'W')
    win_in_one = False
    for r in range(n):
        for c in range(len(grid[r])):
            if grid[r][c] == '.' and makes_five_for_black(grid, r, c):
                win_in_one = True
                break
        if win_in_one:
            break
    return {
        "five_black": bool(five_black),
        "five_white": bool(five_white),
        "black_win_in_one": bool(win_in_one),
        "count_legal": bool(n_black == n_white or n_black == n_white + 1),
        "n_black": int(n_black),
        "n_white": int(n_white),
    }

def position_legal(read):
    """1 if neither side has five in a line and the stone counts are legal, else 0."""
    p = gomoku_props(read['grid'])
    if p['five_black'] or p['five_white'] or not p['count_legal']:
        return 0.0
    return 1.0

# end of gate_code

# code: winf_code
def gomoku_props(grid):
    n = len(grid)
    DIRS = ((0, 1), (1, 0), (1, 1), (1, -1))

    def run_len(g, r, c, dr, dc):
        who = g[r][c]
        if who == '.':
            return 0
        length = 1
        rr, cc = r + dr, c + dc
        while 0 <= rr < n and 0 <= cc < len(g[rr]) and g[rr][cc] == who:
            length += 1
            rr += dr
            cc += dc
        rr, cc = r - dr, c - dc
        while 0 <= rr < n and 0 <= cc < len(g[rr]) and g[rr][cc] == who:
            length += 1
            rr -= dr
            cc -= dc
        return length

    def has_five(g, who):
        for r in range(n):
            for c in range(len(g[r])):
                if g[r][c] != who:
                    continue
                for dr, dc in DIRS:
                    if run_len(g, r, c, dr, dc) >= 5:
                        return True
        return False

    def makes_five_for_black(g, r, c):
        for dr, dc in DIRS:
            length = 1
            rr, cc = r + dr, c + dc
            while 0 <= rr < n and 0 <= cc < len(g[rr]) and g[rr][cc] == 'B':
                length += 1
                rr += dr
                cc += dc
            rr, cc = r - dr, c - dc
            while 0 <= rr < n and 0 <= cc < len(g[rr]) and g[rr][cc] == 'B':
                length += 1
                rr -= dr
                cc -= dc
            if length >= 5:
                return True
        return False

    n_black = sum(row.count('B') for row in grid)
    n_white = sum(row.count('W') for row in grid)
    five_black = has_five(grid, 'B')
    five_white = has_five(grid, 'W')
    win_in_one = False
    for r in range(n):
        for c in range(len(grid[r])):
            if grid[r][c] == '.' and makes_five_for_black(grid, r, c):
                win_in_one = True
                break
        if win_in_one:
            break
    return {
        "five_black": bool(five_black),
        "five_white": bool(five_white),
        "black_win_in_one": bool(win_in_one),
        "count_legal": bool(n_black == n_white or n_black == n_white + 1),
        "n_black": int(n_black),
        "n_white": int(n_white),
    }

def black_wins_in_one(read):
    """1 if black has a winning move on the read board, else 0."""
    return 1.0 if gomoku_props(read['grid'])['black_win_in_one'] else 0.0

# end of winf_code

# code: counts_code
def gomoku_props(grid):
    n = len(grid)
    DIRS = ((0, 1), (1, 0), (1, 1), (1, -1))

    def run_len(g, r, c, dr, dc):
        who = g[r][c]
        if who == '.':
            return 0
        length = 1
        rr, cc = r + dr, c + dc
        while 0 <= rr < n and 0 <= cc < len(g[rr]) and g[rr][cc] == who:
            length += 1
            rr += dr
            cc += dc
        rr, cc = r - dr, c - dc
        while 0 <= rr < n and 0 <= cc < len(g[rr]) and g[rr][cc] == who:
            length += 1
            rr -= dr
            cc -= dc
        return length

    def has_five(g, who):
        for r in range(n):
            for c in range(len(g[r])):
                if g[r][c] != who:
                    continue
                for dr, dc in DIRS:
                    if run_len(g, r, c, dr, dc) >= 5:
                        return True
        return False

    def makes_five_for_black(g, r, c):
        for dr, dc in DIRS:
            length = 1
            rr, cc = r + dr, c + dc
            while 0 <= rr < n and 0 <= cc < len(g[rr]) and g[rr][cc] == 'B':
                length += 1
                rr += dr
                cc += dc
            rr, cc = r - dr, c - dc
            while 0 <= rr < n and 0 <= cc < len(g[rr]) and g[rr][cc] == 'B':
                length += 1
                rr -= dr
                cc -= dc
            if length >= 5:
                return True
        return False

    n_black = sum(row.count('B') for row in grid)
    n_white = sum(row.count('W') for row in grid)
    five_black = has_five(grid, 'B')
    five_white = has_five(grid, 'W')
    win_in_one = False
    for r in range(n):
        for c in range(len(grid[r])):
            if grid[r][c] == '.' and makes_five_for_black(grid, r, c):
                win_in_one = True
                break
        if win_in_one:
            break
    return {
        "five_black": bool(five_black),
        "five_white": bool(five_white),
        "black_win_in_one": bool(win_in_one),
        "count_legal": bool(n_black == n_white or n_black == n_white + 1),
        "n_black": int(n_black),
        "n_white": int(n_white),
    }

def count_stones(read):
    """The total number of black and white stones on the read board."""
    p = gomoku_props(read['grid'])
    return p['n_black'] + p['n_white']

# end of counts_code
