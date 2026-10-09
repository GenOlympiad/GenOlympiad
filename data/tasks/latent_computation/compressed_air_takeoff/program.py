# shared code: code_drops
def read_drop_takeoffs(tag_reads, position_reads, shape_reads, expected, tags_needed):
    """Each bench tag's drop position and shape, joined in tag order for comparison."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def tag(v):
        s = ''.join(c for c in str(v).upper() if c.isalnum())
        return s if s in ('K1', 'K2', 'K3', 'K4') else None
    def pos(v):
        s = ''.join(c for c in str(v).lower() if c.isalpha())
        for w in ('missing', 'top', 'side', 'bottom'):
            if w in s:
                return w
        return None
    def shape(v):
        s = ''.join(c for c in str(v).lower() if c.isalpha())
        for w in ('missing', 'loop', 'straight'):
            if w in s:
                return w
        return None
    try:
        n = int(float(tags_needed))
    except (TypeError, ValueError):
        n = 99
    seen = {}
    for a, b, c in zip(lst(tag_reads), lst(position_reads), lst(shape_reads)):
        k, p, q = tag(a), pos(b), shape(c)
        if k is None or p is None or q is None:
            continue
        if k not in seen:
            seen[k] = 'missing' if 'missing' in (p, q) else p + '-' + q
    if len(seen) < n:
        return {'obs': 'only ' + str(len(seen)) + ' bench tags were read and '
                       + str(n) + ' were needed', 'exp': str(expected)}
    obs = '|'.join(k + ':' + seen[k] for k in sorted(seen))
    out = {'obs': obs, 'exp': str(expected)}
    if obs == str(expected):
        out['verdict'] = ('the two wet-side drops climb off the crown in loops and '
                          'the two dry-side drops tee straight off the flank')
    return out

# end of code_drops

# shared code: code_fall
def read_main_fall(reads, want):
    """Which way the main is read to fall: level, toward the dryer or toward the wall."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    answers = lst(reads)
    s = ''.join(c for c in str(answers[0] if answers else '').lower() if c.isalpha())
    for w in ('level', 'dryer', 'wall'):
        if w in s:
            return {'obs': w, 'exp': str(want)}
    return {'obs': 'the run was not read', 'exp': str(want)}

# end of code_fall

# shared code: code_drip
def read_drain_stub(reads, want):
    """Where the drain stub sits on the main as read: top, side, bottom or missing."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    answers = lst(reads)
    s = ''.join(c for c in str(answers[0] if answers else '').lower() if c.isalpha())
    for w in ('missing', 'bottom', 'side', 'top'):
        if w in s:
            return {'obs': w, 'exp': str(want)}
    return {'obs': 'the stub was not read', 'exp': str(want)}

# end of code_drip
