# shared code: code_8c0f3b41d704
def keyword_match_score(answer, key):
    """Score 1 when the answer contains the expected word and not its opposite."""
    if answer is None: return 0.0
    a = str(answer).strip().lower()
    k = str(key).strip().lower()
    pairs = {'yes': 'no', 'no': 'yes', 'left': 'right', 'right': 'left'}
    opposite = pairs.get(k)
    if opposite and opposite in a and k not in a: return 0.0
    return 1.0 if k in a else 0.0

def headcount(*vals):
    out = 1.0
    for v in vals:
        try: out *= float(v)
        except (TypeError, ValueError): out *= 0.0
    return round(out, 4)

# end of code_8c0f3b41d704
