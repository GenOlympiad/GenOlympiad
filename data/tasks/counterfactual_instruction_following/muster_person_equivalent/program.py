# code: helpers
from genolympiad.task_helpers import (
    count_confirmed_cutouts, paint_cells_by_fraction, plan_pinned_grid)
# end of helpers

# shared code: code_boat_check
import re
def check_boat_loads(names, capacities, totals, lists):
    """Whether each boat's total equals crew at 1.5 plus passengers within capacity."""
    g = lambda x: [str(v).strip().lower() for v in ((x or {}).get('answers') or [])]
    num = lambda s: float((re.findall(r'\d+(?:\.\d+)?', str(s)) or ['-1'])[0])
    results = []
    for b, c, t, l in zip(g(names), g(capacities), g(totals), g(lists)):
        b = ''.join(ch for ch in b if ch.isalnum())
        crew = sum(1 for w in l.split(',') if w.strip().startswith('c'))
        want = 1.5 * crew + sum(1 for w in l.split(',') if w.strip().startswith('p'))
        ok = abs(num(t) - want) < 0.01 and want <= num(c)
        results.append(b + '=' + ('ok' if ok else 'off'))
    placed = len(set(w.strip() for l in g(lists) for w in l.split(',')) - set(['', 'none']))
    good = all(o.endswith('=ok') for o in results) and len(results) > 0 and placed >= 15
    return {'seq': 'ok' if good else 'off', 'n': len(results), 'placed': placed,
            'verdict': ' | '.join(sorted(results)) + ' -> whole board %s, %d distinct codes placed' % ('ok' if good else 'off', placed)}

# end of code_boat_check

# shared code: code_roster_union
def read_roster_codes(node):
    """The person codes written across the columns, with how often each appears."""
    seen, n = {}, 0
    for a in ((node or {}).get('answers') or []):
        for w in str(a).replace(';', ',').split(','):
            t = ''.join(c for c in w.strip().lower() if c.isalnum())
            if t and t != 'none':
                seen[t] = seen.get(t, 0) + 1
                n += 1
    seq = ','.join(t if seen[t] == 1 else t + 'x%d' % seen[t] for t in sorted(seen))
    return {'seq': seq, 'n': n, 'people': len(seen),
            'verdict': '%d code(s) written across the columns, %d of them different'
                       % (n, len(seen))}

# end of code_roster_union
