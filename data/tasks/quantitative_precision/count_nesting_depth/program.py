# shared code: code_fd3860cb34ee

def radius_strips(target_read):
    """Two thin strips from the target centre to its right and left edges."""
    geometry = ((target_read or {}).get('geometry') or [])
    if not geometry:
        return {'geometry': [], 'degenerate': True}
    y0, x0, y1, x1 = [float(v) for v in geometry[0]]
    cy, cx = (y0 + y1) / 2.0, (x0 + x1) / 2.0
    h = max(6.0, 0.02 * (y1 - y0))
    if x1 - cx < 20.0 or cx - x0 < 20.0 or y1 - y0 < 20.0:
        return {'geometry': [], 'degenerate': True}
    return {'geometry': [[cy - h, cx, cy + h, x1], [cy - h, x0, cy + h, cx]],
            'degenerate': False}


def _runs(text, ca, cb):
    import re
    out = []
    for t in re.split(r'[^A-Za-z]+', str(text or '').lower()):
        if not t:
            continue
        c = None
        if t.startswith(ca[:4]):
            c = 'a'
        elif t.startswith(cb[:4]):
            c = 'b'
        if c is None:
            continue
        if out and out[-1] == c:
            continue
        out.append(c)
    return out


def depth_from_words(colour_read, colour_a, colour_b):
    """Count the colour bands along each strip, refusing if the strips disagree."""
    seqs = [_runs(a, colour_a, colour_b) for a in ((colour_read or {}).get('answers') or [])]
    seqs = [s for s in seqs if len(s) >= 2]
    if not seqs:
        return {'depth': None, 'parity': None, 'unreadable': True, 'reason': 'no_colour_words'}
    depths = [len(s) for s in seqs]
    if len(set(depths)) != 1:
        return {'depth': None, 'parity': None, 'unreadable': True,
                'reason': 'chords_disagree', 'depths': depths}
    s = seqs[0]
    n_a = sum(1 for c in s if c == 'a')
    n_b = sum(1 for c in s if c == 'b')
    return {'depth': n_a + n_b, 'a': n_a, 'b': n_b, 'parity': abs(n_a - n_b),
            'unreadable': False, 'depths': depths}

# end of code_fd3860cb34ee
