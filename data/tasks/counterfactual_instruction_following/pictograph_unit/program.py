# code: helpers
from genolympiad.task_helpers import count_as_read, count_confirmed_cutouts
# end of helpers

# code: chk_code
def icon_count_matches(r, want):
    """Full marks when the last number read equals the expected icon count."""
    import re
    answer = (r.get('answers') or [None])[0] if isinstance(r, dict) else r
    if answer is None:
        return {'frac': 0.0, 'n': None, 'want': int(want)}
    text = str(answer).strip().lower()
    words = {'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6,
             'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12,
             'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16,
             'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20}
    m = re.findall(r'-?\d+', text)
    n = int(m[-1]) if m else None
    if n is None:
        for w, v in words.items():
            if w in text:
                n = v
                break
    return {'frac': 1.0 if (n is not None and n == int(want)) else 0.0,
            'n': n, 'want': int(want), 'said': text[:40]}

# end of chk_code

# code: law_code
def whole_and_half_icons(whole_read, half_read, want_whole):
    """Full marks for the right number of whole icons and exactly one half icon."""
    import re
    def _one(r):
        return (r.get('answers') or [None])[0] if isinstance(r, dict) else r
    def _num(a):
        if a is None:
            return None
        m = re.findall(r'-?\d+', str(a))
        if m:
            return int(m[-1])
        words = {'zero': 0, 'none': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}
        s = str(a).strip().lower()
        for w, v in words.items():
            if w in s:
                return v
        return None
    n_whole = _num(_one(whole_read)); n_half = _num(_one(half_read))
    if n_whole is None or n_half is None:
        return {'frac': 0.0, 'whole': n_whole, 'half': n_half}
    f_whole = 1.0 if n_whole == int(want_whole) else 0.0
    f_half = 1.0 if n_half == 1 else 0.0
    return {'frac': f_whole * f_half, 'whole': n_whole, 'half': n_half,
            'want_whole': int(want_whole)}

# end of law_code
