# shared code: code_7d115ff92c36
def punched_rows_per_column(cell_answers, rowlabels, nrows, ncols):
    """The row labels punched in each column, from the per-cell yes or no answers."""
    answers = cell_answers.get('answers') if isinstance(cell_answers, dict) else cell_answers
    n_rows, n_cols = int(nrows), int(ncols)
    if not answers or len(answers) != n_rows * n_cols:
        return {'seq': None, 'cols': None, 'n_holes': None, 'no_read': True}
    yes = []
    for v in answers:
        s = str(v if v is not None else '').strip().lower()
        yes.append(1 if s.startswith('y') else 0)
    cols = []
    for c in range(n_cols):
        cols.append([rowlabels[r] for r in range(n_rows)
                     if r < len(rowlabels) and yes[r * n_cols + c]])
    return {'seq': ' '.join('+'.join(x) if x else '-' for x in cols),
            'cols': cols, 'n_holes': sum(yes), 'no_read': False}

# end of code_7d115ff92c36

# shared code: code_33c45483b0fe
def card_cell_boxes(card_box, nrows, ncols):
    """Cut the boxed card into row by column cell boxes, each shrunk by a margin."""
    geometry = card_box.get('geometry') if isinstance(card_box, dict) else card_box
    if isinstance(card_box, dict) and not card_box.get('confirmed'):
        return {'boxes': None, 'span': None, 'no_read': True}
    if not geometry:
        return {'boxes': None, 'span': None, 'no_read': True}
    ymin, xmin, ymax, xmax = [float(v) for v in geometry[0][:4]]
    h, w = ymax - ymin, xmax - xmin
    n_rows, n_cols = int(nrows), int(ncols)
    if w < 30.0 or h < 30.0 or n_rows < 1 or n_cols < 1:
        return {'boxes': None, 'span': [ymin, xmin, ymax, xmax], 'no_read': True}
    cell_height, cell_width = h / float(n_rows), w / float(n_cols)
    if cell_height < 4.0 or cell_width < 4.0:
        return {'boxes': None, 'span': [ymin, xmin, ymax, xmax], 'no_read': True}
    margin = 0.20
    boxes = []
    for r in range(n_rows):
        for c in range(n_cols):
            boxes.append([ymin + (r + margin) * cell_height, xmin + (c + margin) * cell_width,
                          ymin + (r + 1.0 - margin) * cell_height, xmin + (c + 1.0 - margin) * cell_width])
    return {'boxes': boxes, 'span': [ymin, xmin, ymax, xmax],
            'cell': [round(cell_height, 2), round(cell_width, 2)], 'no_read': False}

# end of code_33c45483b0fe

# code: col_match_code
def columns_match(read, rowlabels, wanted_columns):
    """The share of columns whose punched rows equal the reference, capped at 0.25 unless all match."""
    def from_grid(g):
        grid=g['grid'] if isinstance(g,dict) else g
        if not grid: return None
        R=len(grid); C=len(grid[0])
        cols=[]
        for c in range(C):
            rows=[rowlabels[r] for r in range(R) if r<len(rowlabels) and grid[r][c]]
            cols.append(set(rows))
        return cols
    def from_str(s):
        cols=[]
        for tok in str(s).replace(',',' ').split():
            cols.append(set(p for p in tok.split('+') if p))
        return cols
    got = from_grid(read) if isinstance(read,(dict,list)) else from_str(read)
    if not got: return 0.0
    want=[set(p) for p in wanted_columns]
    ok=sum(1 for i in range(len(want)) if i<len(got) and got[i]==want[i])
    frac=round(ok/len(want),4)
    if ok < len(want): frac=min(frac, 0.25)
    return frac

# end of col_match_code

# code: nholes_code
def hole_count_matches(punched, want):
    """1.0 if the number of punched holes equals the wanted number."""
    cols = punched.get('cols') if isinstance(punched, dict) else punched
    if cols is None:
        return 0.0
    n = sum(len(set(c)) for c in cols)
    return 1.0 if n == int(want) else 0.0

# end of nholes_code
