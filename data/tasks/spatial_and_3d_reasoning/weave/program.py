# code: helpers
from genolympiad.task_helpers import all_items_satisfy, to_float
# end of helpers

# shared code: code_17f0139bd936

def _cyclic_runs(row, sym):
    n = len(row)
    if all(c == sym for c in row):
        return [n]
    start = 0
    while start < n and row[start] == sym and row[(start - 1) % n] == sym:
        start += 1
    out, cur = [], 0
    for k in range(n):
        c = row[(start + k) % n]
        if c == sym:
            cur += 1
        elif cur:
            out.append(cur)
            cur = 0
    if cur:
        out.append(cur)
    return out


def score_weave_grid(strip_reads, premise_reads, plan, n, reference_grid, over, under, shift):
    """Rebuild the read weave grid and score boxes, float lengths, shift and interlacing."""
    n = int(n)
    over, under, shift = int(over), int(under), int(shift)
    if not isinstance(plan, dict) or plan.get('no_plan'):
        return {'no_read': True, 'reason': 'no lattice box', 'frac_cells': 0.0,
                'frac_float': 0.0, 'frac_shift': 0.0, 'frac_interlace': 0.0}
    m, per_row = int(plan['m']), int(plan['per_row'])
    premise_answers = (premise_reads.get('answers') if isinstance(premise_reads, dict) else premise_reads) or []
    yes = sum(1 for a in premise_answers if str(a or '').strip().lower().startswith('y'))
    no = sum(1 for a in premise_answers if str(a or '').strip().lower().startswith('n'))
    if no > yes:
        return {'no_read': True, 'premise_fail': True,
                'reason': ('the committed cell centres do not land on single squares '
                           '(%d of %d anchored strips straddle the drawn cells) -- the cloth '
                           'is not woven at the committed thread count' % (no, len(premise_answers))),
                'frac_cells': 0.0, 'frac_float': 0.0, 'frac_shift': 0.0,
                'frac_interlace': 0.0, 'premise_votes': premise_answers}
    answers = (strip_reads.get('answers') if isinstance(strip_reads, dict) else strip_reads) or []

    def _clean(a, want):
        s = ''.join(c for c in str(a or '').upper() if c in 'DL')
        return s if len(s) == want else None
    rows, n_missing = [], 0
    for i in range(n):
        row = ''
        for c in range(per_row):
            k = i * per_row + c
            piece = _clean(answers[k], m) if k < len(answers) else None
            if piece is None:
                n_missing += 1
                piece = '?' * m
            row += piece
        rows.append(row.replace('D', 'V').replace('L', 'H'))
    if n_missing >= n * per_row:
        return {'no_read': True, 'reason': 'every strip refused', 'frac_cells': 0.0,
                'frac_float': 0.0, 'frac_shift': 0.0, 'frac_interlace': 0.0,
                'n_missing': n_missing}
    got = rows
    reference_rows = [str(r) for r in reference_grid]
    hit = sum(1 for i in range(n) for j in range(n) if got[i][j] == reference_rows[i][j])
    accuracy = hit / float(n * n)
    flatgt = ''.join(reference_rows)
    base = max(flatgt.count('H'), flatgt.count('V')) / float(len(flatgt))
    cells = max(0.0, (accuracy - base) / max(1e-9, 1.0 - base))
    ok_float = 0
    for row in got:
        if (_cyclic_runs(row, 'H') and all(r == over for r in _cyclic_runs(row, 'H'))
                and _cyclic_runs(row, 'V') and all(r == under for r in _cyclic_runs(row, 'V'))):
            ok_float += 1
    ok_shift = 0
    for i in range(n - 1):
        want = got[i][-shift:] + got[i][:-shift] if shift % n else got[i]
        if got[i + 1] == want:
            ok_shift += 1
    n_interlaced = 0
    for i in range(n):
        col = ''.join(got[k][i] for k in range(n))
        n_interlaced += 1 if ('H' in got[i] and 'V' in got[i]) else 0
        n_interlaced += 1 if ('H' in col and 'V' in col) else 0
    return {'no_read': False, 'grid': got, 'gt_grid': reference_rows, 'n_missing': n_missing,
            'n_cells_correct': hit, 'n_cells': n * n,
            'cell_accuracy': round(accuracy, 4), 'chance_baseline': round(base, 4),
            'frac_cells': round(cells, 4),
            'frac_float': round(ok_float / float(n), 4),
            'frac_shift': round(ok_shift / float(max(1, n - 1)), 4),
            'frac_interlace': round(n_interlaced / float(2 * n), 4)}

# end of code_17f0139bd936

# shared code: code_a0a64a5fb043

def plan_lattice_strips(image, lattice, n):
    """Cut the lattice box into row strips of a few boxes each, plus three premise strips."""
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

    n = int(n)
    lattice_boxes = lattice.get('geometry') if isinstance(lattice, dict) else lattice
    if not lattice_boxes:
        return {'no_plan': True}
    y0, x0, y1, x1 = [float(v) for v in lattice_boxes[0][:4]]
    if x1 - x0 < 50 or y1 - y0 < 50:
        return {'no_plan': True}
    size = _wh(image)
    W, H = size if size else (1000.0, 1000.0)
    px0, px1 = x0 * W / 1000.0, x1 * W / 1000.0
    py0, py1 = y0 * H / 1000.0, y1 * H / 1000.0
    circles = [[(j + 0.5) / n, (i + 0.5) / n, 0.45 / n]
               for i in range(n) for j in range(n)]
    m = 1
    for k in range(2, 6):
        if n % k == 0:
            m = k
    chunks = []
    for i in range(n):
        ry0 = y0 + (y1 - y0) * i / float(n)
        ry1 = y0 + (y1 - y0) * (i + 1) / float(n)
        for j in range(0, n, m):
            cx0 = x0 + (x1 - x0) * j / float(n)
            cx1 = x0 + (x1 - x0) * (j + m) / float(n)
            chunks.append([ry0, cx0, ry1, cx1])
    premise = []
    for i in (0, n // 2, n - 1):
        ry0 = y0 + (y1 - y0) * i / float(n)
        ry1 = y0 + (y1 - y0) * (i + 1) / float(n)
        premise.append([ry0, x0, ry1, x0 + (x1 - x0) * m / float(n)])
    return {'no_plan': False, 'circles': circles, 'm': m, 'per_row': n // m,
            'found_anchors': [[px0, py0], [px1, py0], [px1, py1], [px0, py1]],
            'chunks': {'geometry': chunks}, 'premise_chunks': {'geometry': premise},
            'frame': [W, H]}

# end of code_a0a64a5fb043
