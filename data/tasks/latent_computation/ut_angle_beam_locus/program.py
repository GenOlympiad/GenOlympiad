# shared code: code_path_shape
def beam_path_shape(ans, want):
    """The shape word the judge VLM gave for the drawn beam path, next to the wanted one."""
    def as_list(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    a = as_list(ans)
    letters = ''.join(c for c in str(a[0] if a else '').lower() if c.isalpha())
    for w in ('missing', 'several', 'elsewhere', 'straight', 'floor'):
        if w in letters:
            return {'obs': w, 'exp': str(want)}
    return {'obs': 'the drawn beam line was not read', 'exp': str(want)}

# end of code_path_shape

# shared code: code_landing
def flaw_landing(band, pos, want):
    """Where the flaw mark sits (plate band and beam segment), next to the wanted place."""
    def as_list(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    band_answers, segment_answers = as_list(band), as_list(pos)
    band_letters = ''.join(c for c in str(band_answers[0] if band_answers else '').lower() if c.isalpha())
    segment_letters = ''.join(c for c in str(segment_answers[0] if segment_answers else '').lower() if c.isalpha())
    if not band_letters or not segment_letters:
        return {'obs': 'the flaw mark was not read', 'exp': str(want)}
    if 'outside' in band_letters:
        band_place = 'outside the plate'
    elif 'edge' in band_letters:
        band_place = 'on the bottom edge'
    elif 'top' in band_letters:
        band_place = 'top half'
    elif 'bottom' in band_letters:
        band_place = 'bottom half'
    else:
        band_place = 'no mark'
    segment_place = 'none'
    for w in ('first', 'second', 'off'):
        if w in segment_letters:
            segment_place = w
            break
    if band_place == 'no mark' or segment_place == 'none':
        return {'obs': 'no flaw mark is drawn', 'exp': str(want)}
    obs = band_place + ' / ' + segment_place
    out = {'obs': obs, 'exp': str(want)}
    if obs == str(want):
        out['verdict'] = ('the flaw mark rides the second, rising segment in the top '
                          'half of the plate, where the folded 70 mm path ends')
    return out

# end of code_landing

# shared code: code_screen_mark
def screen_mark_number(ans, want):
    """The scale number read off the flaw screen, next to the wanted one."""
    def as_list(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    a = as_list(ans)
    digits = ''.join(c for c in str(a[0] if a else '') if c.isdigit())
    if not digits:
        return {'obs': 'no scale number was read', 'exp': str(want)}
    digits = digits.lstrip('0') or '0'
    return {'obs': digits, 'exp': str(want)}

# end of code_screen_mark
