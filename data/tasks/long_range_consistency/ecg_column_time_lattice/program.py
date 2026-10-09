# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_listed_items
# end of helpers

# shared code: code_time_lattice
def read_window_states(keys, bursts, aligns, want):
    """Read each pinned window as a burst, aligned or apart, quiet, or unread."""
    def as_list(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def digits_of(v):
        return ''.join(c for c in str(v) if c.isdigit())
    key_digits = [digits_of(k) for k in as_list(keys)]
    burst_answers = [str(b).strip().lower() for b in as_list(bursts)]
    align_answers = [str(a).strip().lower() for a in as_list(aligns)]
    want = [str(w) for w in as_list(want)]
    rows = align_by_printed_key([{'key': k, 'b': b, 'a': a}
                                 for k, b, a in zip(key_digits, burst_answers, align_answers)], want)
    states = []
    for i, w in enumerate(want):
        r = rows[i] if i < len(rows) and isinstance(rows[i], dict) else {}
        b, a = str(r.get('b') or ''), str(r.get('a') or '')
        if 'burst' in b:
            states.append('%s=burst/%s' % (w, 'aligned' if a.startswith('y') else 'apart'))
        elif 'stead' in b:
            states.append('%s=quiet' % w)
        else:
            states.append('%s=unread' % w)
    return {'s': ','.join(states), 'verdict': 'the windows read %s' % (','.join(states) or 'nothing')}

# end of code_time_lattice
