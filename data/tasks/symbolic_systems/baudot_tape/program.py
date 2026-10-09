# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_9cbfd71b2db4
import re
def slice_tape_columns(tape_box, n_cols):
    """Cut the boxed tape into equal-width boxes, one per data column."""
    g = (tape_box or {}).get('geometry') or []
    if not g:
        return []
    y0, x0, y1, x1 = [float(v) for v in g[0]][:4]
    n = int(n_cols)
    if n <= 0 or x1 <= x0:
        return []
    w = (x1 - x0) / n
    return [[y0, x0 + i * w, y1, x0 + (i + 1) * w] for i in range(n)]

def score_punched_columns(column_reads, reference):
    """Share of tape columns punched as the reference code, capped at 0.25 if any is wrong."""
    want = reference['grid']
    ntr = len(want)
    ncols = len(want[0])
    answers = (column_reads or {}).get('answers') or []
    got = []
    for a in answers:
        m = re.search(r'[01]{%d}' % ntr, str(a or '').replace(' ', ''))
        got.append([int(ch) for ch in m.group(0)] if m else None)
    if len(got) != ncols or any(c is None for c in got):
        return {'frac': 0.0, 'no_read': True,
                'verdict': 'a tape column did not read as five punch positions'}
    want_cols = [[want[t][c] for t in range(ntr)] for c in range(ncols)]
    ok = sum(1 for c in range(ncols) if got[c] == want_cols[c])
    frac = round(ok * 1.0 / ncols, 4)
    if ok < ncols:
        frac = min(frac, 0.25)
    return {'frac': frac, 'no_read': False,
            'read': [''.join(str(b) for b in c) for c in got],
            'want': [''.join(str(b) for b in c) for c in want_cols],
            'verdict': '%d of %d ITA2 columns punched correctly -> frac %s'
                       % (ok, ncols, frac)}

def column_count_matches(n_columns, want):
    """Full credit if the number of data columns counted equals the spec."""
    try:
        got = int(round(float(n_columns)))
    except Exception:
        return {'frac': 0.0, 'read': None, 'verdict': 'column count did not read'}
    return {'frac': 1.0 if got == int(want) else 0.0, 'read': got,
            'verdict': 'read %d data columns, spec %d' % (got, int(want))}

# end of code_9cbfd71b2db4
