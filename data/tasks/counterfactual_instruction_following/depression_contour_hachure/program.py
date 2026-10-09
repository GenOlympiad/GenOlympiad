# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: senses_code
def read_tick_directions(keys, reads):
    """List each stake letter with whether its ticks point towards or away."""
    stake_keys = [str(a).strip().upper() for a in ((keys or {}).get('answers') or [])]
    directions = [str(a).strip().lower() for a in ((reads or {}).get('answers') or [])]
    got = []
    for k, s in zip(stake_keys, directions):
        got.append('%s=%s' % (k, s if s in ('towards', 'away') else 'unread'))
    got.sort()
    return {'s': ','.join(got), 'verdict': 'the ticks read %s' % (','.join(got) or 'nothing at all')}

# end of senses_code

# code: inner_code
def read_innermost_heights(keys, reads):
    """List each stake letter with the height read on its innermost contour."""
    stake_keys = [str(a).strip().upper() for a in ((keys or {}).get('answers') or [])]
    heights = [''.join(c for c in str(a) if c.isdigit() or c == '.') for a in ((reads or {}).get('answers') or [])]
    heights = [(v.rstrip('0').rstrip('.') if '.' in v else v) for v in heights]
    got = ['%s=%s' % (k, s) for k, s in zip(stake_keys, heights)]
    got.sort()
    return {'s': ','.join(got), 'verdict': 'the innermost rings read %s' % (','.join(got) or 'nothing at all')}

# end of inner_code
