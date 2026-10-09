# code: upright_ok_code
def upright_ok(corner, bars, want_corner, want_bars):
    """Yes if the upright copy shows the square corner and bar edge the reference expects."""
    def one(n):
        return str((((n or {}).get('answers') or [''])[0]) or '').strip().lower().replace(' ', '-')
    dead = ('', 'none', 'n-a', 'na', 'empty', 'nil', 'blank', 'unknown', 'unclear')
    corner_read, bars_read = one(corner), one(bars)
    good = corner_read not in dead and bars_read not in dead and corner_read == str(want_corner).lower() and bars_read == str(want_bars).lower()
    return {'ok': 'yes' if good else 'no',
            'verdict': 'the upright copy carries its square at %s and its bars along the %s edge' % (corner_read or 'nothing', bars_read or 'nothing')}

# end of upright_ok_code

# code: carried_through_code
def carried_through(flat_corner, flat_bars, upright_corner, upright_bars):
    """Yes if the upright copy matches the flat copy taken through the hanging rule."""
    def one(n):
        return str((((n or {}).get('answers') or [''])[0]) or '').strip().lower().replace(' ', '-')
    corner_map = {'top-left': 'top-left', 'top-right': 'bottom-left', 'bottom-left': 'top-right', 'bottom-right': 'bottom-right'}
    bars_map = {'top': 'left', 'bottom': 'right', 'left': 'top', 'right': 'bottom'}
    fcv, fbv, ucv, ubv = one(flat_corner), one(flat_bars), one(upright_corner), one(upright_bars)
    good = fcv in corner_map and fbv in bars_map and corner_map[fcv] == ucv and bars_map[fbv] == ubv
    return {'ok': 'yes' if good else 'no',
            'verdict': 'the flat copy taken through the convention gives square %s and bars %s, and the upright copy shows square %s and bars %s' % (corner_map.get(fcv, 'nothing'), bars_map.get(fbv, 'nothing'), ucv or 'nothing', ubv or 'nothing')}

# end of carried_through_code

# code: hung_code
def flag_hung_upright(node):
    """Yes if the answer says a flag hangs long side upright on the atrium wall."""
    a = ((node or {}).get('answers') or [''])
    s = str(a[0] if a else '').strip().lower()
    dead = ('', 'none', 'n a', 'na', 'empty', 'nil', 'blank', 'not filled', 'unknown', 'unclear')
    v = 'yes' if (s not in dead and s.startswith('y')) else 'no'
    return {'s': v, 'verdict': 'a flag hangs with its long side upright on the atrium wall: %s' % v}

# end of hung_code
