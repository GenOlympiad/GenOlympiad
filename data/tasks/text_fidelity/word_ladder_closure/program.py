# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
def norm(s): return ''.join(ch for ch in str(s).upper() if ch.isalpha())
def ham1(x, y):
    if len(x) != len(y) or not x: return False
    diff=sum(1 for a,b in zip(x,y) if a!=b)
    return diff == 1
def check_ladder_steps(a0, b0, a1, b1):
    """1.0 if both word pairs are read and each pair differs by exactly one letter."""
    A0=norm(a0); B0=norm(b0); A1=norm(a1); B1=norm(b1)
    if not all((A0,B0,A1,B1)): return 0.0
    if not ham1(A0, B0): return 0.0
    if not ham1(A1, B1): return 0.0
    return 1.0

# end of law_code
