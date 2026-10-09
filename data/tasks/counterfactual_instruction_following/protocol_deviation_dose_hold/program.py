# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_visit_rows
import re
def visit_dose_rows(visits, planned, given, sep):
    """Pair each visit with its planned and given dose, sorted by visit."""
    g = lambda x: [str(v).strip().lower() for v in ((x or {}).get('answers') or [])]
    n1 = lambda s: (re.findall(r'\d+(?:\.\d+)?', s) or ['none'])[0]
    a, b, d = g(planned), g(given), {}
    for i, t in enumerate([''.join(c for c in w if c.isalnum()) for w in g(visits)]):
        if t and t not in d:
            d[t] = n1(a[i] if i < len(a) else '') + sep + n1(b[i] if i < len(b) else '')
    seq = ','.join(t + '=' + d[t] for t in sorted(d))
    return {'rows': [[t, d[t]] for t in sorted(d)], 'seq': seq, 'n': len(d),
            'verdict': '%d visit block(s) read as protocol|given' % len(d)}

# end of code_visit_rows

# shared code: code_named_visits
def logged_visits(node, skip):
    """List the distinct visits named on the log lines, leaving out the empty word."""
    out = []
    for a in ((node or {}).get('answers') or []):
        t = ''.join(c for c in str(a).strip().lower() if c.isalnum())
        if t and t != skip and t not in out:
            out.append(t)
    return {'seq': ','.join(sorted(out)), 'n': len(out),
            'verdict': '%d entry line(s) name a visit -> %s'
                       % (len(out), '/'.join(sorted(out)) or 'none')}

# end of code_named_visits
