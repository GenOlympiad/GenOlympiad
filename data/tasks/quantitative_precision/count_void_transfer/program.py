# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_2a7924a29f02
def count_ratio_gap(a, b, k, off):
    """How far count b is from k times count a plus an offset, 999 if either is missing."""
    if a is None or b is None:
        return 999
    return abs(b - (k * a + off))

def implausible(a, b, minimum):
    """1 if either count is missing or below the minimum, else 0."""
    return 1 if (a is None or b is None or a < minimum or b < minimum) else 0

# end of code_2a7924a29f02

# code: floor_score_code
def floor_score(count, minimum):
    """Full credit at or above the minimum count, minus a third per missing item."""
    if count is None:
        return 0.0
    if count >= minimum:
        return 1.0
    return max(0.0, 1.0 - (minimum - count) / 3.0)

# end of floor_score_code
