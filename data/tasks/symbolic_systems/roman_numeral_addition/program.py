# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_2efb0b2d1759
def _first_answer(r):
    if isinstance(r, dict):
        a = r.get('answers') or [None]
        return a[0]
    return r
def read_roman(reads):
    """The longest run of Roman numeral letters in the first answer, or an empty string."""
    import re
    answer = _first_answer(reads)
    if answer is None:
        return ''
    tokens = []
    for w in re.split(r'\s+', str(answer)):
        s = re.sub(r'[^IVXLCDM]', '', str(w).upper())
        if s:
            tokens.append(s)
    return max(tokens, key=len) if tokens else ''

# end of code_2efb0b2d1759

# shared code: code_b68b3b4a6f93
def roman_int(s):
    """The value of a correctly written Roman numeral below 4000, or None otherwise."""
    values = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}
    ENC = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
    def to_roman(n):
        o=''
        for v,sym in ENC:
            while n>=v: o+=sym; n-=v
        return o
    if not s or any(ch not in values for ch in str(s)):
        return None
    total=prev=0
    for ch in reversed(str(s)):
        v=values[ch]; total += v if v>=prev else -v; prev=v
    if total<=0 or total>=4000 or to_roman(total)!=str(s):
        return None
    return total

# end of code_b68b3b4a6f93
