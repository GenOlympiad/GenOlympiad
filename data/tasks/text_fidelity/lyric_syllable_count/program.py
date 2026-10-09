# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_listed_items
# end of helpers

# code: chk_code
def beats_equal_syllables(n0, s0, n1, s1, n2, s2, n3, s3):
    """1 if each of the four bars has as many note beats as syllables, else 0."""
    pairs = [(n0, s0), (n1, s1), (n2, s2), (n3, s3)]
    for (n, s) in pairs:
        try:
            if int(round(float(n))) != int(round(float(s))):
                return 0.0
        except Exception:
            return 0.0
    return 1.0

# end of chk_code
