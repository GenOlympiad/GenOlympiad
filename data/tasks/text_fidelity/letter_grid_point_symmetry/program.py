# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
def one(s):
    t=''.join(ch for ch in str(s).upper() if ch.isalpha())
    return t[0] if t else None
def mirror_pairs_match(a0, b0, a1, b1):
    """1 if both pairs of point-mirrored letters are the same letter, else 0."""
    A0=one(a0); B0=one(b0); A1=one(a1); B1=one(b1)
    if None in (A0, B0, A1, B1): return 0.0
    if A0 != B0: return 0.0
    if A1 != B1: return 0.0
    return 1.0

# end of law_code
