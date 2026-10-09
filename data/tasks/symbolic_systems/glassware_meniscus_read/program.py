# code: chk_code
def reading_matches(answer, want):
    """1 if any number in the answer equals the reference mL reading, else 0."""
    import re
    if answer is None or isinstance(answer, dict): return 0.0
    s = str(answer).strip().lower()
    s = s.replace('milliliters', ' ').replace('millilitres', ' ')
    s = re.sub(r'\bm\s*l\b', ' ', s)
    numbers = re.findall(r'-?\d+(?:\.\d+)?', s)
    if not numbers: return 0.0
    try:
        want_v = float(want)
    except (TypeError, ValueError):
        return 0.0
    for tok in numbers:
        if abs(float(tok) - want_v) < 1e-9:
            return 1.0
    return 0.0

# end of chk_code
