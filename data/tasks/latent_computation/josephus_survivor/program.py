# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: same_code
def circled_equals_boxed(circled, boxed):
    """1 if the circled seat number equals the boxed seat number, else 0."""
    try:
        a = int(round(float(circled)))
        b = int(round(float(boxed)))
    except (TypeError, ValueError):
        return 0.0
    return 1.0 if a == b else 0.0

# end of same_code
