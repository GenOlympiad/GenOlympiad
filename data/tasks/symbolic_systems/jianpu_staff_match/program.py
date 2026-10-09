# code: law_code

def staff_contour_score(noteheads, pairs, targets, n_cols, eps=0.012):
    """Score 1 when every queried pair of staff noteheads rises or falls as the numbers say."""
    if not noteheads or noteheads.get('unreadable'):
        return {'frac': 0.0, 'verdict': 'noteheads unreadable'}
    geometry = noteheads.get('geometry') or []
    n = int(n_cols)
    if len(geometry) != n:
        return {'frac': 0.0, 'n_found': len(geometry),
                'verdict': 'staff carries %d noteheads, the piece has %d columns' % (len(geometry), n)}
    cols = sorted(geometry, key=lambda b: (b[1] + b[3]) / 2.0)
    ys = [((b[0] + b[2]) / 2.0) / 1000.0 for b in cols]
    reads, ok = [], 1.0
    for (a, b), target in zip(pairs, targets):
        a, b = int(a), int(b)
        d = ys[a] - ys[b]
        relation = 'higher' if d > eps else ('lower' if d < -eps else 'same')
        reads.append('col%d vs col%d: %s (want %s)' % (b + 1, a + 1, relation, str(target).lower()))
        if relation != str(target).lower():
            ok = 0.0
    return {'frac': ok, 'verdict': '; '.join(reads) + ' -> %s' % ('MATCH' if ok else 'CONTOUR BROKEN')}

# end of law_code

# code: m_code
def first_digit_score(answer, target):
    """Score 1 when the first digit in the answer equals the expected digit."""
    if answer is None: return 0.0
    import re
    a=re.sub(r'[^0-9]','',str(answer))
    return 1.0 if a[:1]==str(target) else 0.0

# end of m_code
