# shared code: code_329ac6922bad
_WORD = {'arch': 'down', 'bowl': 'up', 'straight': 'flat'}


def _read(node):
    out = []
    for a in ((node or {}).get('answers') or []):
        s = str(a or '').strip().lower()
        hit = None
        for w in ('arch', 'bowl', 'straight'):
            if w in s:
                hit = _WORD[w]
                break
        out.append(hit)
    return out


def count_strips(node, k):
    """Score 1 if the number of strips read equals the expected count."""
    reads = _read(node)
    n = sum(1 for x in reads if x is not None)
    return {'frac': 1.0 if n == int(k) else 0.0, 'n_strips': n, 'asked': len(reads),
            'k': int(k), 'read': reads}


def score_bend_directions(node, expected):
    """Score the bend directions read against the expected ones, scaled so chance level gives 0."""
    directions = [x or 'flat' for x in _read(node)]
    want = [str(x) for x in expected]
    if len(directions) != len(want):
        return {'frac': 0.0, 'dirs': directions, 'expected': want, 'hits': None}
    hits = sum(1 for a, b in zip(directions, want) if a == b)
    share = hits / float(len(want))
    return {'frac': round(max(0.0, (share - 0.5) / 0.5), 4), 'dirs': directions, 'expected': want,
            'hits': hits, 'k': len(want)}

# end of code_329ac6922bad

# shared code: code_ff00105ff9d8
def order_strips(node):
    """Sort the strip boxes top to bottom if stacked, else left to right."""
    boxes = [list(map(float, b)) for b in ((node or {}).get('geometry') or [])]
    if not boxes:
        return {'geometry': [], 'n': 0, 'layout': None}
    cy = [(b[0] + b[2]) / 2.0 for b in boxes]
    cx = [(b[1] + b[3]) / 2.0 for b in boxes]
    stacked = (max(cy) - min(cy)) >= (max(cx) - min(cx))
    idx = sorted(range(len(boxes)), key=(lambda i: (cy[i], cx[i])) if stacked
                 else (lambda i: (cx[i], cy[i])))
    return {'geometry': [[int(round(v)) for v in boxes[i]] for i in idx], 'n': len(boxes),
            'layout': 'stacked' if stacked else 'row'}

# end of code_ff00105ff9d8
