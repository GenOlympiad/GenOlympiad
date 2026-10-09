# shared code: starcode
def worst_tip_spacing_error(centers, ntips):
    """Largest deviation of the star tip angles from even spacing, in degrees."""
    import math as _m
    N = int(ntips)
    if centers is None or len(centers) != N+1:
        return 90.0
    P = [(float(a), float(b)) for a, b in centers]
    gx = sum(p[0] for p in P)/len(P)
    gy = sum(p[1] for p in P)/len(P)
    ci = min(range(len(P)), key=lambda i: (P[i][0]-gx)**2 + (P[i][1]-gy)**2)
    cx, cy = P[ci]
    tips = [P[i] for i in range(len(P)) if i != ci]
    angs = sorted(_m.degrees(_m.atan2(-(y-cy), x-cx)) % 360 for (x, y) in tips)
    step = 360.0/N
    gaps = [(angs[(k+1) % N] - angs[k]) % 360 for k in range(N)]
    return round(max(abs(g - step) for g in gaps), 4)

# end of starcode

# code: count_yes_code
def count_yes(node):
    """Count the yes answers among the per box checks."""
    answers = (node or {}).get('answers') or []
    yes = [a for a in answers if str(a or '').strip().lower().startswith('yes')]
    return {'n': len(yes), 'asked': len(answers), 'answers': [str(a) for a in answers],
            'why': 'one atomic yes/no per confirmed rectangle, summed in code'}

# end of count_yes_code

# code: centres_code
def centres(boxes, src):
    """The pixel centre of every confirmed dot box."""
    W, H = src.size
    g = (boxes or {}).get('geometry') or []
    C = []
    for b in g:
        y0, x0, y1, x1 = [float(v) for v in b]
        C.append([(x0 + x1) / 2.0 * W / 1000.0, (y0 + y1) / 2.0 * H / 1000.0])
    return {'centers': C, 'n': len(C), 'degenerate': len(C) < 3,
            'why': 'centre of each confirmed black-dot rectangle, in pixels'}

# end of centres_code
