# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_seq_join
def join_readings(node):
    """Join the cut-out readings, cleaned to letters and digits, with bars."""
    rows = []
    for raw in (node or {}).get('answers') or []:
        txt = ''.join(c if c.isalnum() else ' ' for c in str(raw).lower())
        rows.append(' '.join(txt.split()))
    return {'seq': '|'.join(rows), 'n': len(rows),
            'verdict': 'the cut-outs read %s' % ('|'.join(rows) or 'nothing')}

# end of code_seq_join

# shared code: code_restated_map
def entry_pairs_by_key(keys, vals, want):
    """Pair each line's date and country key with the restated date read on that line."""
    def lst(n):
        a = n.get('answers') if isinstance(n, dict) else None
        return list(a) if isinstance(a, (list, tuple)) else []
    def norm(x):
        return ' '.join(''.join(c if c.isalnum() else ' ' for c in str(x).lower()).split())
    def keyof(x):
        s = str(x).lower()
        digs = ''.join(c for c in s if c.isdigit())
        country = ' '.join(''.join(c if c.isalpha() else ' ' for c in s).split())
        return (digs + ' ' + country).strip()
    pairs = []
    for k, v in zip(lst(keys), lst(vals)):
        kk, vv = keyof(k), norm(v)
        if kk or vv:
            pairs.append('%s=%s' % (kk, vv))
    return {'pairs': pairs, 'n': len(pairs),
            'verdict': 'entry lines keyed by their own invoice date and country: %s' % ('; '.join(pairs) or 'nothing')}

# end of code_restated_map
