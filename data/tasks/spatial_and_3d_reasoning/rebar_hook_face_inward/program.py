# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_tie_hooks
def check_tie_hooks(k, d, c, keys, want_direction):
    """Count ties with hooks facing the wanted way plus hook corners that alternate tie to tie."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def pick(v, opts):
        if v is None:
            return None
        s = ' '.join(str(v).lower().replace('-', ' ').split())
        if s in ('', 'none', 'n a', 'na', 'nil', 'empty', '?', '.'):
            return None
        for o in opts:
            if o in s:
                return o
        return None
    want = [str(x) for x in lst(keys)]
    got = align_by_printed_key([{'key': x, 'd': a, 'c': b}
                                for x, a, b in zip(lst(k), lst(d), lst(c))], want)
    corners = ['near left', 'near right', 'far left', 'far right']
    n, seq, notes = 0, [], []
    for i, row in enumerate(got):
        r = row if isinstance(row, dict) else {}
        pd = pick(r.get('d'), ['inward', 'outward', 'no hook visible'])
        if pd is not None and pd == str(want_direction).lower():
            n += 1
        pc = pick(r.get('c'), corners)
        seq.append(pc)
        notes.append('tie %s hook %r at %r' % (want[i] if i < len(want) else i, pd, pc))
    for a, b in zip(seq, seq[1:]):
        if a is not None and b is not None and a != b:
            n += 1
    notes.append('corner run %r' % (seq,))
    return {'n': n, 'checks': 2 * len(want) - 1, 'verdict': '; '.join(notes)}

# end of code_tie_hooks
