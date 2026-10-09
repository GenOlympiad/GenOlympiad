# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_port_lines
def port_temperatures(node):
    """The temperature read at each hot and cold port, and whether cold out tops hot out."""
    import re
    temps = {}
    for a in (node or {}).get('answers') or []:
        s = str(a).lower()
        m = re.search(r'\d+(?:\.\d+)?', s.replace(',', ''))
        if m and ('hot' in s or 'cold' in s) and (' in' in s or 'out' in s):
            temps[('h' if 'hot' in s else 'c') + ('o' if 'out' in s else 'i')] = float(m.group(0))
    pairs = '|'.join(sorted('%s:%g' % kv for kv in temps.items()))
    crossing = 'yes' if temps.get('co', 0) > temps.get('ho', 1e9) else 'no'
    return {'pairs': pairs, 'crossing': crossing, 'verdict': 'ports %s, cold out above hot out: %s' % (pairs or '(none)', crossing)}

# end of code_port_lines
