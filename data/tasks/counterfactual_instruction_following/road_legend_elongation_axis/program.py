# shared code: code_stretch_axis
def legend_arrow_offset(letters, arrows, sepmin):
    """Worst angle between each legend and its arrow, 90 if the two lanes sit too close."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def clock(v):
        s = ''.join(c for c in str(v) if c.isdigit())
        if not s:
            return None
        h = int(s[:2]) if len(s) > 2 else int(s)
        if h < 1 or h > 12:
            return None
        return (h % 12) * 30.0
    def fold(x):
        x = x % 180.0
        return 180.0 - x if x > 90.0 else x
    letter_angles = [clock(v) for v in lst(letters)]
    arrow_angles = [clock(v) for v in lst(arrows)]
    pairs = [(a, b) for a, b in zip(letter_angles, arrow_angles) if a is not None and b is not None]
    try:
        need = float(sepmin)
    except (TypeError, ValueError):
        need = 60.0
    if len(pairs) < 2:
        return {'obs': 90.0, 'exp': 0.0, 'n': float(len(pairs)),
                'verdict': 'fewer than two lanes could be read, so the pairing is undefined'}
    offsets = [fold(a - b) for a, b in pairs[:2]]
    sep = fold(pairs[0][0] - pairs[1][0])
    worst = max(offsets)
    if sep < need:
        worst = 90.0
    return {'obs': worst, 'exp': 0.0, 'sep': sep, 'n': float(len(pairs)),
            'verdict': 'legend against its own arrow is off by ' + str(offsets)
                       + ' and the two long axes stand ' + str(sep)
                       + ' apart, which needs at least ' + str(need)}

# end of code_stretch_axis

# shared code: code_letter_shape
def letters_stretched(shape_reads, want):
    """Say whether both legends read as stretched letter shapes."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    seen = []
    for v in lst(shape_reads):
        s = ''.join(c for c in str(v).lower() if c.isalpha())
        if 'stretch' in s:
            seen.append('stretched')
        elif 'ordinary' in s or 'square' in s:
            seen.append('ordinary')
    exp = str(want).strip().lower()
    if len(seen) < 2:
        return {'obs': 'unread', 'exp': exp,
                'verdict': 'fewer than two legends gave a readable letter shape'}
    got = 'both' if all(s == 'stretched' for s in seen[:2]) else 'not both'
    return {'obs': got, 'exp': exp,
            'verdict': 'letter shapes read as ' + str(seen[:2]) + ', which is ' + got}

# end of code_letter_shape
