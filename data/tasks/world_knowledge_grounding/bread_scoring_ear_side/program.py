# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_key_match_count
def ear_match(keys, vals, loaves, oven, want):
    """Count loaves whose ears open toward the oven, or evenly where the reference says so."""
    wanted = dict(p.split('=') for p in str(want).split('|') if p.count('=') == 1)
    keys_read = [''.join(c for c in str(a) if c.isdigit())
          for a in ((keys or {}).get('answers') or [])]
    values_read = [str(a).strip().lower().replace('-', ' ')
          for a in ((vals or {}).get('answers') or [])]
    def geo(n):
        g = (n or {}).get('geometry') if isinstance(n, dict) else None
        return [b for b in (g or []) if isinstance(b, (list, tuple)) and len(b) >= 4]
    loaf_boxes, oven_boxes = geo(loaves), geo(oven)
    oven_x = (float(oven_boxes[0][0]) + float(oven_boxes[0][2])) / 2.0 if oven_boxes else None
    n, notes = 0, []
    for i, (k, s) in enumerate(zip(keys_read, values_read)):
        t = str(wanted.get(k, '')).strip().lower()
        if not t or not s:
            notes.append('loaf %s could not be read' % (k or '?'))
            continue
        if 'evenly' in t:
            if 'even' in s:
                n += 1
                notes.append('loaf %s should open evenly and reads %r' % (k, s))
            else:
                notes.append('loaf %s should open evenly but reads %r' % (k, s))
        elif oven_x is None or i >= len(loaf_boxes):
            notes.append('loaf %s: the oven or the loaf box was not read' % k)
        else:
            lx = (float(loaf_boxes[i][0]) + float(loaf_boxes[i][2])) / 2.0
            side = 'left' if oven_x < lx else 'right'
            if side in s and 'even' not in s:
                n += 1
                notes.append('loaf %s: the oven stands to the %s on the page and the ears read '
                           '%r' % (k, side, s))
            else:
                notes.append('loaf %s: the oven stands to the %s on the page but the ears read '
                           '%r' % (k, side, s))
    return {'n': n, 'asked': len(values_read),
            'verdict': '; '.join(notes) or 'nothing was read'}

# end of code_key_match_count

# shared code: code_key_pair_frac
def match_pinned_states(keys, vals, want):
    """Score each tagged loaf's read cut run against the reference, one value per tag."""
    wanted = dict(p.split('=') for p in str(want).split('|') if p.count('=') == 1)
    keys_read = [str(a).strip().upper().replace(' ', '') for a in ((keys or {}).get('answers') or [])]
    values_read = [str(a).strip().lower().replace('-', ' ') for a in ((vals or {}).get('answers') or [])]
    matches = {}
    for k, s in zip(keys_read, values_read):
        t = str(wanted.get(k, '')).strip().lower()
        matches[k] = 1.0 if (t and s and t in s) else 0.0
    wanted_keys = sorted(wanted)
    return {'a': matches.get(wanted_keys[0], 0.0) if wanted_keys else 0.0, 'b': matches.get(wanted_keys[1], 0.0) if len(wanted_keys) > 1 else 0.0, 'c': matches.get(wanted_keys[2], 0.0) if len(wanted_keys) > 2 else 0.0, 'verdict': 'each pinned half of the conjunction reads %s' % sorted(matches.items())}

# end of code_key_pair_frac
