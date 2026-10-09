# code: helpers
from genolympiad.task_helpers import count_as_read, count_confirmed_cutouts
# end of helpers

# code: chk_code
def _first_answer(r):
    if isinstance(r, dict):
        a = r.get('answers') or [None]
        return a[0]
    return r
def count_matches_span(count_read, want):
    """Full credit if the count read equals the reference span, else zero."""
    import re
    a = _first_answer(count_read)
    if a is None or isinstance(a, dict):
        return {'frac': 0.0, 'read': None, 'want': int(want)}
    s = str(a).strip().lower()
    words = {'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6,
             'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12,
             'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16}
    ms = re.findall(r'-?\d+', s)
    n = int(ms[-1]) if ms else None
    if n is None:
        for w, v in words.items():
            if w in s:
                n = v
                break
    return {'frac': 1.0 if (n is not None and n == int(want)) else 0.0,
            'read': n, 'want': int(want)}

# end of chk_code
