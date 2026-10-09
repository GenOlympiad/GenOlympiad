# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: j_code
def j(mp,bl,gpos,gcap):
    """1 if the red token square matches and blue is present exactly when not captured."""
    try: okp = abs(float(mp)-float(gpos))<0.5
    except Exception: return 0.0
    blue_present = isinstance(bl,str) and bl.strip().lower().startswith('yes')
    okb = (blue_present == (not gcap))
    return 1.0 if (okp and okb) else 0.0

# end of j_code
