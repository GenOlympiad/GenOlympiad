# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: worst_gap_code
def worst_tick_gap(keys, ticks, want):
    """The largest angle between a drawn dip tick and the dip direction its reading calls for."""
    bearing_of = {'top': 0.0, 'top right': 45.0, 'right': 90.0, 'bottom right': 135.0,
         'bottom': 180.0, 'bottom left': 225.0, 'left': 270.0, 'top left': 315.0}
    wanted = dict(p.split('=') for p in str(want).split(',') if p.count('=') == 1)
    keys_read = [str(a).strip().upper() for a in ((keys or {}).get('answers') or [])]
    ticks_read = [str(a).strip().lower().replace('-', ' ') for a in ((ticks or {}).get('answers') or [])]
    gaps = [180.0] * (len(wanted) - min(len(keys_read), len(ticks_read)))
    for k, s in zip(keys_read, ticks_read):
        t = wanted.get(k)
        gaps.append(180.0 if (s not in bearing_of or t is None) else abs((bearing_of[s] - float(t) + 180.0) % 360.0 - 180.0))
    return {'gap': max(gaps or [180.0]), 'verdict': 'the worst of the three ticks sits %.0f degrees from the dip direction its own reading calls for' % max(gaps or [180.0])}

# end of worst_gap_code

# code: axis_gap_code
def worst_bar_gap(keys, bars, want):
    """The largest angle between a drawn strike bar and the strike bearing booked for it."""
    bearing_of = {'up and down': 0.0, 'lower left to upper right': 45.0,
         'left and right': 90.0, 'upper left to lower right': 135.0}
    wanted = dict(p.split('=') for p in str(want).split(',') if p.count('=') == 1)
    keys_read = [str(a).strip().upper() for a in ((keys or {}).get('answers') or [])]
    bars_read = [str(a).strip().lower() for a in ((bars or {}).get('answers') or [])]
    gaps = [90.0] * (len(wanted) - min(len(keys_read), len(bars_read)))
    for k, s in zip(keys_read, bars_read):
        t = wanted.get(k)
        gaps.append(90.0 if (s not in bearing_of or t is None) else abs((bearing_of[s] - float(t) + 90.0) % 180.0 - 90.0))
    return {'gap': max(gaps or [90.0]), 'verdict': 'the worst of the three bars lies %.0f degrees off the strike bearing booked for it' % max(gaps or [90.0])}

# end of axis_gap_code
