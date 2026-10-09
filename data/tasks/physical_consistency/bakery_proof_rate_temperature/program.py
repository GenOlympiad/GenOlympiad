# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_prove
def _keyed(t, v, num=True):
    import re
    ta = t.get('answers') if isinstance(t, dict) else None
    va = v.get('answers') if isinstance(v, dict) else None
    ta = list(ta) if isinstance(ta, (list, tuple)) else []
    va = list(va) if isinstance(va, (list, tuple)) else []
    ks = [re.search(r'\d+', str(a)) for a in ta]
    rows = {}
    for k, a in zip(ks, va):
        if not k:
            continue
        if num:
            m = re.search(r'\d+(?:[.,]\d+)?', str(a).replace(',', '.'))
            rows[int(k.group())] = float(m.group()) if m else None
        else:
            rows[int(k.group())] = str(a or '').strip().lower().startswith('sunk')
    return rows

def rise_then_fall(temp_reads, level_reads, cool, mid, hot):
    """Half a point each for the middle tub rising above the cool and the hot tub."""
    rows = _keyed(temp_reads, level_reads)
    cool_level, mid_level, hot_level = rows.get(int(cool)), rows.get(int(mid)), rows.get(int(hot))
    up = 1 if (cool_level is not None and mid_level is not None and mid_level > cool_level) else 0
    down = 1 if (mid_level is not None and hot_level is not None and mid_level > hot_level) else 0
    return {'rows': rows, 'hits': up + down, 'frac': (up + down) / 2.0,
            'verdict': 'levels %s -- rises to the middle shelf: %s, falls back on the hottest: %s' % (rows, bool(up), bool(down))}

def sunk_tops_match(temp_reads, top_reads, hot):
    """Share of tubs whose sunken top reading is right: only the hottest may sink."""
    rows = _keyed(temp_reads, top_reads, num=False)
    want = int(hot)
    hits = sum(1 for k, sunk in rows.items() if sunk == (k == want))
    return {'rows': rows, 'hits': hits, 'frac': hits / float(len(rows) or 1),
            'verdict': 'sunken tops read %s; only %s C may be sunk' % (rows, want)}

# end of code_prove
