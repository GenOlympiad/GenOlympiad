# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_last_fit
def last_edge_gap(printed_keys, straight, inner, ball, heel, sheet_order):
    """Worst clock angle gap between each last's straight side and the outline's inside edge."""
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
    def hour(v):
        d = ''.join(c for c in str(v) if c.isdigit())
        x = int(d) if d and len(d) <= 2 else None
        return x if x is not None and 1 <= x <= 12 else None
    want = [str(x) for x in lst(sheet_order)]
    got = align_by_printed_key([{'key': x, 's': a, 'i': b, 'b': c, 'h': d}
                                for x, a, b, c, d in zip(lst(printed_keys), lst(straight), lst(inner),
                                                         lst(ball), lst(heel))], want)
    worst, facts, say = 0.0, 0, []
    for i, row in enumerate(got):
        r = row if isinstance(row, dict) else {}
        hs, hi = hour(r.get('s')), hour(r.get('i'))
        if hs is None or hi is None:
            return {'obs': 180.0, 'exp': 0.0, 'facts': facts,
                    'verdict': 'sheet %s edges not read' % (want[i] if i < len(want) else i)}
        d = abs(((hs % 12) * 30.0 - (hi % 12) * 30.0 + 180.0) % 360.0 - 180.0)
        worst = d if d > worst else worst
        for key in ('b', 'h'):
            if pick(r.get(key), ['yes', 'no']) == 'yes':
                facts += 1
        say.append('sheet %s straight side at %d against outline inside at %d'
                   % (want[i], hs, hi))
    return {'obs': worst, 'exp': 0.0, 'facts': facts, 'verdict': '; '.join(say)}

# end of code_last_fit
