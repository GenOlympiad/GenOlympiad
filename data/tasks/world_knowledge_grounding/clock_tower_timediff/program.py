# shared code: code_6bbc6cd556e9
def hour_offset_matches(london_read, tokyo_read, offset):
    """1.0 if the two clock hours differ by the reference offset either way, else 0.0."""
    import re
    def hour_of(x):
        m = re.search(r'(\d{1,2})', str(x));
        return int(m.group(1)) % 12 if m else None
    a, b = hour_of(london_read), hour_of(tokyo_read)
    if a is None or b is None: return 0.0
    d = (b - a) % 12
    target = int(offset) % 12
    return 1.0 if d == target or (12 - d) % 12 == target else 0.0

# end of code_6bbc6cd556e9
