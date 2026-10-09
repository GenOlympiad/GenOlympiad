# code: law_code
def norm(s):
    t = ''.join(ch for ch in str(s).lower() if ch.isalnum())
    import re
    m = re.search(r'([a-h][1-8])', t)
    return m.group(1) if m else ''
def pieces_on_required_squares(ws, bs, want_ws, want_bs):
    """1 if the two read squares match the required white and black squares, else 0."""
    ws = norm(ws); bs = norm(bs)
    WS = str(want_ws).lower(); BS = str(want_bs).lower()
    if ws != WS:
        return 0.0
    if bs != BS:
        return 0.0
    return 1.0

# end of law_code
