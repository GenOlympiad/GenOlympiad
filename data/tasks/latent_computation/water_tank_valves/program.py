# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: extreme_code
def extreme_tank_score(cells, target, want_max):
    """Score 1 when the single fullest (or emptiest) tank read is the expected tank."""
    rows = (cells or {}).get('values') or []
    levels = []
    for r in rows:
        v = r[0] if isinstance(r, (list, tuple)) and r else r
        try:
            levels.append(float(v))
        except (TypeError, ValueError):
            return {'frac': 0.0, 'unreadable': True, 'read': None, 'levels': None}
    if not levels:
        return {'frac': 0.0, 'unreadable': True, 'read': None, 'levels': None}
    extreme_level = max(levels) if want_max else min(levels)
    hits = [i for i, v in enumerate(levels) if v == extreme_level]
    if len(hits) != 1:
        return {'frac': 0.0, 'unreadable': False, 'read': 'tie(%s)' % ','.join(
            str(i + 1) for i in hits), 'want': str(target), 'levels': levels}
    got = str(hits[0] + 1)
    return {'frac': 1.0 if got == str(target).strip() else 0.0, 'unreadable': False,
            'read': got, 'want': str(target).strip(), 'levels': levels}

# end of extreme_code
