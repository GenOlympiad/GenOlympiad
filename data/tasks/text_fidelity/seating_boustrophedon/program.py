# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
def seat_numbers_match(v0, v1, v2, v3, s_val):
    """1 if the four sampled seat numbers match the snake order values, else 0."""
    reads = [v0, v1, v2, v3]
    want = [int(x) for x in s_val]
    for got, w in zip(reads, want):
        try:
            g = float(got)
        except Exception:
            return 0.0
        if abs(g - w) > 0.5:
            return 0.0
    return 1.0

# end of law_code
