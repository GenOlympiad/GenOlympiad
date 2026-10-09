# code: chk_code
import re
def check_makes_24(expr, dealt_numbers):
    """Score 1 when the expression uses exactly the dealt numbers and evaluates to 24."""
    s = str(expr or '')
    for a, b in (('\u00d7','*'),('x','*'),('X','*'),('\u00b7','*'),('\u00f7','/'),(':','/')): s = s.replace(a, b)
    s = s.split('=')[0]
    if sorted(int(t) for t in re.findall(r'\d+', s)) != sorted(int(c) for c in dealt_numbers): return 0.0
    if not re.fullmatch(r'[0-9+\-*/() ]+', s): return 0.0
    try: v = eval(s, {'__builtins__': {}}, {})
    except Exception: return 0.0
    return 1.0 if abs(float(v) - 24.0) < 1e-6 else 0.0

# end of chk_code

# code: cards_match_code
import re


def numbers_match(answer, dealt_numbers):
    """Score 1 when the numbers read from the answer are exactly the dealt numbers."""
    if answer is None:
        return 0.0
    got = sorted(int(t) for t in re.findall(r'\d+', str(answer)))
    want = sorted(int(c) for c in (dealt_numbers or []))
    return 1.0 if (want and got == want) else 0.0

# end of cards_match_code
