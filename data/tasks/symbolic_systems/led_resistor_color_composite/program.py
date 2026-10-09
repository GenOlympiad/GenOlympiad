# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: decode_code
def band_value_matches(band_read, want_ohm):
    """1 if the colour bands read decode to the reference resistance in ohms."""
    DIG = {'black': 0, 'brown': 1, 'red': 2, 'orange': 3, 'yellow': 4, 'green': 5,
           'blue': 6, 'violet': 7, 'purple': 7, 'grey': 8, 'gray': 8, 'white': 9}
    ans = (band_read or {}).get('answers') or []
    s = str(ans[0] if ans else '').strip().lower()
    if not s:
        return {'frac': 0.0, 'seq': [], 'ohm': None, 'why': 'no sequence read'}
    words = []
    cur = ''
    for ch in s:
        if ch.isalpha():
            cur += ch
        else:
            if cur:
                words.append(cur)
            cur = ''
    if cur:
        words.append(cur)
    metal = ('gold', 'silver')
    toks = [w for w in words if w in DIG or w in metal]
    if toks and toks[0] in metal and toks[-1] not in metal:
        toks = toks[::-1]
    val = [w for w in toks if w not in metal]
    if len(val) < 3:
        return {'frac': 0.0, 'seq': toks, 'ohm': None, 'why': 'fewer than 3 value bands'}
    d1, d2, mul = val[0], val[1], val[2]
    r = (DIG[d1] * 10 + DIG[d2]) * (10 ** DIG[mul])
    return {'frac': 1.0 if abs(r - float(want_ohm)) < 0.5 else 0.0, 'seq': toks, 'ohm': r,
            'want': float(want_ohm)}

# end of decode_code
