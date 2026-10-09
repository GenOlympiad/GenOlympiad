# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
def digits6(s):
    t=''.join(ch for ch in str(s) if ch.isdigit())
    return t[:6] if len(t)>=6 else None
def chk(s):
    t=str(s).strip().upper()
    t=''.join(ch for ch in t if ch.isalnum())
    return t[-1] if t else None
def expect(body):
    W=[7,6,5,4,3,2]
    tot=sum(int(d)*w for d,w in zip(body,W))
    c=(11-(tot%11))%11
    return 'X' if c==10 else str(c)
def check_digits_match(body0, chk0, body1, chk1):
    """1 if both sampled IDs carry the check digit their six digits require, else 0."""
    b0=digits6(body0); b1=digits6(body1)
    c0=chk(chk0); c1=chk(chk1)
    if None in (b0,b1,c0,c1): return 0.0
    if expect(b0) != c0: return 0.0
    if expect(b1) != c1: return 0.0
    return 1.0

# end of law_code
