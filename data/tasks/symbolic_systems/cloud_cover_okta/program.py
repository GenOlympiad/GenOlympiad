# shared code: code_a6894f9b25b0
def to_eighths(reads):
    """Read the stated number of shaded eighths from the first answer."""
    import re
    answer = (reads.get('answers') or [None])[0] if isinstance(reads, dict) else reads
    if answer is None:
        return {'eighths': None, 'no_read': True}
    m = re.search(r'-?\d+(?:\.\d+)?', str(answer))
    if not m:
        return {'eighths': None, 'no_read': True}
    v = float(m.group(0))
    return {'eighths': v, 'no_read': False, 'said': str(answer)[:60]}

# end of code_a6894f9b25b0

# code: chk_code
def feather_count_score(reads, want):
    """Score 1 when the read number of full feathers equals the expected number."""
    import re
    answer = (reads.get('answers') or [None])[0] if isinstance(reads, dict) else reads
    if answer is None:
        return {'frac': 0.0, 'read': None, 'want': int(want)}
    m = re.search(r'-?\d+', str(answer))
    n = int(m.group(0)) if m else None
    return {'frac': 1.0 if (n is not None and n == int(want)) else 0.0,
            'read': n, 'want': int(want)}

# end of chk_code

# code: both_code
def combined_score(fill_frac, feather_frac):
    """Multiply the fill score by the feather score, each clamped to 0 to 1."""
    def f(x):
        try:
            return max(0.0, min(1.0, float(x)))
        except (TypeError, ValueError):
            return 0.0

    return round(f(fill_frac) * f(feather_frac), 4)

# end of both_code
