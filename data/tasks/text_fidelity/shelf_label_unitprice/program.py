# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
import re
def _money(a):
    m = re.search(r'(\d+)[.,](\d{2})\b', str(a))
    if m:
        return int(m.group(1)) * 100 + int(m.group(2))
    m = re.search(r'\b(\d+)\b', str(a))
    return int(m.group(1)) * 100 if m else None
def _int(a):
    m = re.search(r'\b(\d+)\b', str(a))
    return int(m.group(1)) if m else None
def _first_answer(r):
    if isinstance(r, dict):
        a = r.get('answers') or [None]
        return a[0]
    return r
def unit_price_check(a_pack, a_size, a_unit, want_pack_c, want_size, want_unit_c):
    """1 if pack price, size and unit price read right and unit price is pack over size."""
    p, s, u = _money(_first_answer(a_pack)), _int(_first_answer(a_size)), _money(_first_answer(a_unit))
    if p is None or s is None or u is None:
        return {'frac': 0.0, 'read': [p, s, u], 'why': 'a field did not read'}
    ok = (abs(p - int(want_pack_c)) <= 1 and s == int(want_size)
          and abs(u - int(want_unit_c)) <= 1
          and s != 0 and abs(u - round(p * 1.0 / s)) <= 1)
    return {'frac': 1.0 if ok else 0.0, 'read': [p, s, u],
            'want': [int(want_pack_c), int(want_size), int(want_unit_c)]}

# end of law_code
