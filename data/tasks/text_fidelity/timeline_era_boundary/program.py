# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
def iv(s):
    import re
    m=re.search(r'-?\d+', str(s).replace(',',''))
    return int(m.group()) if m else None
def check_era_boundary(end_i, start_j, start_i, end_j, decreasing):
    """1.0 if one era ends where the next starts and both run in the stated direction."""
    ei=iv(end_i); sj=iv(start_j); si=iv(start_i); ej=iv(end_j)
    if None in (ei, sj, si, ej): return 0.0
    if ei != sj: return 0.0
    if decreasing:
        if not (si > ei): return 0.0
        if not (sj > ej): return 0.0
    else:
        if not (ei > si): return 0.0
        if not (ej > sj): return 0.0
    return 1.0

# end of law_code
