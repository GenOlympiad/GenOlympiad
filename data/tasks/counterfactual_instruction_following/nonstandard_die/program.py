# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# shared code: code_c675a44b01e6
def count_matches_reference(answer, want):
    """Score 1 if the number in the answer equals the expected count."""
    import re
    if answer is None or isinstance(answer, dict):
        return 0.0
    t = str(answer).strip().lower()
    words = {'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12}
    m = re.search(r'-?\d+', t)
    n = int(m.group(0)) if m else None
    if n is None:
        for w,v in words.items():
            if w in t: n = v; break
    return 1.0 if (n is not None and n == int(want)) else 0.0

# end of code_c675a44b01e6

# code: face_n_code

def read_face_pips(close_up_read):
    """The number of pips read on one face of the die."""
    import re
    a = (close_up_read.get('answers') if isinstance(close_up_read, dict) else close_up_read) or []
    t = a[0] if a else None
    if t is None:
        return {'n': None, 'verdict': 'the close-up of the die came back with no answer'}
    m = re.search(r'-?\d+', str(t))
    if not m:
        return {'n': None,
                'verdict': 'the close-up answer held no number: %s' % str(t)[:60]}
    n = int(m.group(0))
    return {'n': n, 'verdict': 'the close-up of the die read %d dots on that face' % n}

# end of face_n_code
