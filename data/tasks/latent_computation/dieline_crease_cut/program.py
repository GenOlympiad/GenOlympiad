# shared code: code_lines
def read_sheet_lines(fold_read, tab_read, slot_read, place_read, want):
    """Join the fold, tab and slot line styles and slot position read, against the reference."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def style(v):
        s = ''.join(c for c in str(v).lower() if c.isalpha())
        for w in ('missing', 'mixed', 'dashed', 'solid'):
            if w in s:
                return w
        return None
    def station(v):
        s = ''.join(c for c in str(v).lower() if c.isalpha())
        if 'noslot' in s or 'missing' in s:
            return 'none'
        if 'side' in s:
            return 'side walls'
        if 'base' in s:
            return 'base'
        if 'tab' in s:
            return 'tabs'
        return None
    a = style((lst(fold_read) or [''])[0])
    b = style((lst(tab_read) or [''])[0])
    c = style((lst(slot_read) or [''])[0])
    d = station((lst(place_read) or [''])[0])
    if None in (a, b, c, d):
        return {'obs': 'the pattern sheet was not fully read', 'exp': str(want)}
    observed = a + '/' + b + '/' + c + '/' + d
    out = {'obs': observed, 'exp': str(want)}
    if observed == str(want):
        out['verdict'] = ('folds dashed, slots knife-cut and standing inside the '
                          'side walls, exactly as the folding forces')
    return out

# end of code_lines

# shared code: code_sample
def read_tray_sample(corner_read, open_read, want):
    """Join how the tray corners hold and whether it opens, against the reference."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def corner(v):
        s = ''.join(c for c in str(v).lower() if c.isalpha())
        for w in ('missing', 'loose', 'pinched', 'tucked'):
            if w in s:
                return w
        return None
    def yn(v):
        s = ''.join(c for c in str(v).lower() if c.isalpha())
        for w in ('missing', 'yes', 'no'):
            if w in s:
                return w
        return None
    c = corner((lst(corner_read) or [''])[0])
    opens = yn((lst(open_read) or [''])[0])
    if c is None or opens is None:
        return {'obs': 'the finished tray was not read', 'exp': str(want)}
    observed = c + '/' + opens
    out = {'obs': observed, 'exp': str(want)}
    if observed == str(want):
        out['verdict'] = 'every corner holds by its own tab through its own slot'
    return out

# end of code_sample
