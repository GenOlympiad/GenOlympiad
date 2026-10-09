# shared code: code_bafc124918c3
def square_marking_matches(answer, expected):
    """Score 1 if the square reads blue or plain as expected."""
    if answer is None: return 0.0
    a = str(answer).strip().lower()
    want = str(expected).strip().lower()
    is_blue = 'blue' in a or 'highlight' in a
    is_plain = 'plain' in a or 'no ' in a or 'not ' in a
    if want == 'blue':
        return 1.0 if (is_blue and not is_plain) else 0.0
    return 1.0 if (is_plain and not is_blue) else 0.0

def headcount(*vals):
    out = 1.0
    for v in vals:
        try: out *= float(v)
        except (TypeError, ValueError): out *= 0.0
    return round(out, 4)

# end of code_bafc124918c3
