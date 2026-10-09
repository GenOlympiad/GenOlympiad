# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# code: chk_code
def leg_count_matches(ans, want):
    """Full marks when the first number read equals the expected leg count."""
    import re
    if ans is None or isinstance(ans, dict):
        return 0.0
    t = str(ans).strip().lower()
    words = {'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9}
    m = re.search(r'-?\d+', t)
    n = int(m.group(0)) if m else None
    if n is None:
        for w,v in words.items():
            if w in t: n = v; break
    return 1.0 if (n is not None and n == int(want)) else 0.0

# end of chk_code
