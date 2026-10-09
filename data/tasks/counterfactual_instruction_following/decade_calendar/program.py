# code: chk_code
def column_heading_matches(answer, want):
    """Score 1 if the read column heading contains the expected day name."""
    if answer is None or isinstance(answer, dict): return 0.0
    t = str(answer).strip().lower()
    w = str(want).strip().lower()
    return 1.0 if w in t else 0.0

# end of chk_code
