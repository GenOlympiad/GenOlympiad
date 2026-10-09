# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_row_bind
def bind_row_values(key_reads, value_reads, separator, skip_word):
    """Pair each row id with what that row says, skipping blanks and a given skip word."""
    g = lambda x: [str(v).strip().lower() for v in ((x or {}).get('answers') or [])]
    k, v, bound = g(key_reads), g(value_reads), {}
    for i, t in enumerate(k):
        t = ''.join(c for c in t if c.isalnum())
        w = ''.join(c for c in (v[i] if i < len(v) else '') if c.isalnum())
        if t and w and w != skip_word and t not in bound:
            bound[t] = w
    seq = ','.join(t + separator + bound[t] for t in sorted(bound))
    return {'rows': [[t, bound[t]] for t in sorted(bound)], 'seq': seq, 'n': len(bound),
            'verdict': '%d row(s) bound to what that row of the page says' % len(bound)}

# end of code_row_bind

# shared code: code_selective_pair
def selected_rows_match(key_reads, value_reads, expected_pairs, named_rows):
    """Whether every named row reads the value the concession expects for it."""
    g = lambda x: [str(v).strip().lower() for v in ((x or {}).get('answers') or [])]
    k, v, bound = g(key_reads), g(value_reads), {}
    for i, t in enumerate(k):
        t = ''.join(c for c in t if c.isalnum())
        if t and t not in bound:
            bound[t] = ''.join(c for c in (v[i] if i < len(v) else '') if c.isalnum())
    want = dict(p.split('=') for p in str(expected_pairs).split(',') if '=' in p)
    checked = [r for r in str(named_rows).split(',') if r]
    good = bool(checked) and all(bound.get(r) == want.get(r) for r in checked)
    return {'seq': 'ok' if good else 'off', 'n': len(checked),
            'verdict': ' | '.join('%s reads %s, the concession wants %s' % (r, bound.get(r) or 'nothing', want.get(r)) for r in checked)}

# end of code_selective_pair
