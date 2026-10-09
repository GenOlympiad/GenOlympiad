# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: tallest_code
def tallest_bin_matches(bin_reads, want):
    """1 if the bin with the largest read value is the reference tallest bin, else 0."""
    vals = []
    rows = bin_reads.get('values') if isinstance(bin_reads, dict) else bin_reads
    if not isinstance(rows, (list, tuple)) or not rows:
        return 0.0
    for r in rows:
        v = r[0] if isinstance(r, (list, tuple)) and r else r
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            return 0.0
    best = max(vals)
    idx = vals.index(best)
    try:
        target = int(str(want).strip())
    except (TypeError, ValueError):
        return 0.0
    return 1.0 if (idx + 1) == target else 0.0

# end of tallest_code
