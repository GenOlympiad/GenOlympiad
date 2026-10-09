# shared code: code_517dcdbd76ed
def lit_side_matches(answer, expected):
    """Score 1 if the lit side read is only the expected top or bottom."""
    if answer is None: return 0.0
    a = str(answer).strip().lower()
    said_bottom = ('bottom' in a) or ('below' in a) or ('lower' in a)
    said_top = ('top' in a) or ('above' in a) or ('upper' in a)
    want = str(expected).strip().lower()
    if want == 'bottom':
        return 1.0 if (said_bottom and not said_top) else 0.0
    return 1.0 if (said_top and not said_bottom) else 0.0

def headcount(*vals):
    out = 1.0
    for v in vals:
        try: out *= float(v)
        except (TypeError, ValueError): out *= 0.0
    return round(out, 4)

# end of code_517dcdbd76ed
