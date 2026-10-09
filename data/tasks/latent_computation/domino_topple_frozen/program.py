# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: up_code
def first_letters_upper(seq):
    """Keep the upper-cased first letter of each read row."""
    return [[str(r[0]).strip().upper()[:1]] for r in seq]

# end of up_code

# code: joint_code
import re
def pick(a):
    if not isinstance(a, str): return None
    s = a.strip().lower()
    m = re.match(r'^[\(\[]?([ab])[\)\].:,\s]', s + ' ')
    if m: return m.group(1)
    m = re.search(r'\boption\s*([ab])\b', s)
    if m: return m.group(1)
    m = re.search(r'\b([ab])\b', s)
    if m: return m.group(1)
    return None
def both_picked_a(pf, pl):
    """Score 1 when both picked answers come back as option a."""
    f = pick(pf); l = pick(pl)
    if f is None or l is None: return 0.0
    return 1.0 if (f == 'a' and l == 'a') else 0.0

# end of joint_code

# code: count_f_code
def count_f_rows(seq):
    """Count the read rows whose letter is F."""
    if not isinstance(seq, (list, tuple)):
        return None
    n = 0
    for r in seq:
        tok = r[0] if isinstance(r, (list, tuple)) and r else r
        if str(tok).strip().upper()[:1] == 'F':
            n += 1
    return n

# end of count_f_code
