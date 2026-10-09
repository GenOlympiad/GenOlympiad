# shared code: code_dbd7a3e4c85f
def read_handedness(handedness_read, located_read):
    """Whether the writing reads normal or mirrored, and whether its position was confirmed."""
    a = ((handedness_read or {}).get('answers') or [None])[0]
    s = str(a or '').strip().lower()
    if 'mirror' in s or 'back' in s or 'revers' in s:
        v = 'mirrored'
    elif 'normal' in s:
        v = 'normal'
    else:
        v = ''
    b = ((located_read or {}).get('answers') or [None])[0]
    ok = str(b or '').strip().lower().startswith('y')
    return {'val': v, 'raw': s, 'located': ok,
            'note': 'read position proven' if ok else 'read position unproven'}

# end of code_dbd7a3e4c85f

# code: collapse_code
def handedness_differs(a, b):
    """Score 1 only if the two surfaces read with opposite handedness."""
    x, y = (a or {}).get('val'), (b or {}).get('val')
    if not x or not y:
        return {'frac': 0.0, 'crash': 'handedness unreadable', 'paint': x, 'card': y}
    if x == y:
        name = ('everything drawn readable' if x == 'normal'
                else 'whole frame mirrored')
        return {'frac': 0.0, 'crash': name, 'paint': x, 'card': y}
    return {'frac': 1.0, 'crash': None, 'paint': x, 'card': y}

# end of collapse_code
