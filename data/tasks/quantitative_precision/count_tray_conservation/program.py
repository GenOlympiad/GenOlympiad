# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# code: count_left_tray_code
import re
def count_left_tray(node):
    """Read the number of cookies counted on the left tray, refusing if none."""
    answer = ((node or {}).get('answers') or [None])[0]
    if answer is None: return {'n': None, 'no_read': True, 'refused': True, 'verdict': 'the tray count did not read'}
    m = re.findall(r'\d+', str(answer))
    if not m: return {'n': None, 'no_read': True, 'refused': True, 'verdict': 'the tray count answered %r, which carries no number' % (answer,)}
    n = int(m[0])
    return {'n': n, 'no_read': False, 'verdict': 'the reader counted %d cookies on this tray' % n}

# end of count_left_tray_code

# code: count_right_tray_code
import re
def count_right_tray(node):
    """Read the number of cookies counted on the right tray, refusing if none."""
    answer = ((node or {}).get('answers') or [None])[0]
    if answer is None: return {'n': None, 'no_read': True, 'refused': True, 'verdict': 'the tray count did not read'}
    m = re.findall(r'\d+', str(answer))
    if not m: return {'n': None, 'no_read': True, 'refused': True, 'verdict': 'the tray count answered %r, which carries no number' % (answer,)}
    n = int(m[0])
    return {'n': n, 'no_read': False, 'verdict': 'the reader counted %d cookies on this tray' % n}

# end of count_right_tray_code
