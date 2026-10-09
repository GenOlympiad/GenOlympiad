# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: chk_code
def row_counts_match(seq, reference):
    """Score 1 when the first three read row counts equal the reference counts."""
    if not isinstance(seq, list) or len(seq) < 3: return 0.0
    try:
        got = [int(str(x)) for x in seq[:3]]
    except (TypeError, ValueError):
        return 0.0
    return 1.0 if got == [int(v) for v in reference] else 0.0

# end of chk_code

# code: chk_code_2
def row_counts_close(a, b, c, reference):
    """Score 1 when the three read row counts match the reference, allowing 1 above eight."""
    counts = [a, b, c]
    if any(v is None or isinstance(v, dict) for v in counts):
        return 0.0
    try:
        got = [round(float(v)) for v in counts]
    except (TypeError, ValueError):
        return 0.0
    want = [int(v) for v in reference]
    for g, w in zip(got, want):
        tol = 0 if w <= 8 else 1
        if abs(g - w) > tol:
            return 0.0
    return 1.0

# end of chk_code_2
