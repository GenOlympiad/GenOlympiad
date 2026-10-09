# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
import re
def parse(s):
    m=re.search(r'(\d+)\s*[-:]\s*(\d+)', str(s))
    return (int(m.group(1)), int(m.group(2))) if m else None
def results_mirror(ij0, ji0, ij1, ji1):
    """1 if both result pairs read are mirror images across the diagonal, else 0."""
    for a, b in ((ij0, ji0), (ij1, ji1)):
        pa=parse(a); pb=parse(b)
        if pa is None or pb is None: return 0.0
        if pb != (pa[1], pa[0]): return 0.0
    return 1.0

# end of law_code
