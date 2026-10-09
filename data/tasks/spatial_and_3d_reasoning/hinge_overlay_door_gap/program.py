# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_door_ledger
def check_door_widths(labels, values):
    """Check the two door widths plus reveals and centre joint exactly close the 900 mm front."""
    import re
    widths = {}
    for t, v in zip((labels or {}).get('answers') or [], (values or {}).get('answers') or []):
        if (m := re.search(r'\d+(?:\.\d+)?', str(v))): widths[re.sub(r'[^a-z]+', '', str(t).lower())] = float(m.group(0))
    left, right = widths.get('l'), widths.get('r')
    if left is None or right is None: return {'state': 'incomplete', 'verdict': 'the two door width rows could not be read'}
    front = 2.0 + left + 3.0 + right + 2.0
    if abs(left - right) > 0.01: return {'state': 'uneven', 'verdict': 'the two leaves differ (%.1f vs %.1f) -- the pair hangs lopsided' % (left, right)}
    if front > 900.05: return {'state': 'clash', 'verdict': 'the doors hang %.1f proud of the 900 front -- they slam into each other' % (front - 900.0)}
    if front < 899.95: return {'state': 'gap', 'verdict': 'the doors hang %.1f short of the 900 front -- carcass board shows beside them' % (900.0 - front)}
    return {'state': 'closes', 'verdict': 'two leaves of %.1f close the 900 front with the standard reveals and centre joint' % left}

# end of code_door_ledger
