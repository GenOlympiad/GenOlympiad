# shared code: code_28e749270126
def is_roman_numeral(ans, key):
    """Full marks when the field reads as Roman numeral letters only, with no digits."""
    if ans is None: return 0.0
    a = str(ans).strip().upper()
    a = a.replace('|', 'I').replace('!', 'I').replace('L', 'L')
    import re
    a = re.sub(r'[^A-Z0-9]', '', a)
    if a == '': return 0.0
    if any(ch.isdigit() for ch in a):
        return 0.0
    return 1.0 if all(ch in 'IVXLCDMN' for ch in a) else 0.0

def headcount(*vals):
    out = 1.0
    for v in vals:
        try: out *= float(v)
        except (TypeError, ValueError): out *= 0.0
    return round(out, 4)

# end of code_28e749270126
