# shared code: code_864e7b5d6038
def arrow_points_expected(answer, expected):
    """Score 1 if the read arrow direction is the expected one."""
    if answer is None: return 0.0
    a = str(answer).strip().lower()
    k = str(expected).strip().lower()
    others = [d for d in ['up','down','left','right'] if d != k]
    if any(o in a for o in others) and k not in a: return 0.0
    return 1.0 if k in a else 0.0

def headcount(*vals):
    out = 1.0
    for v in vals:
        try: out *= float(v)
        except (TypeError, ValueError): out *= 0.0
    return round(out, 4)

# end of code_864e7b5d6038
