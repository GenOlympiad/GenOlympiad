# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: chk_code
def bar_ends_match(a0, a1, b0, b1, A0, A1, B0, B1):
    """1 if all four bar ends read as the reference start and end values."""
    values = [a0, a1, b0, b1]
    if any(v is None or isinstance(v, dict) for v in values):
        return 0.0
    try:
        got = [round(float(v)) for v in values]
    except (TypeError, ValueError):
        return 0.0
    want = [int(A0), int(A1), int(B0), int(B1)]
    return 1.0 if got == want else 0.0

# end of chk_code
