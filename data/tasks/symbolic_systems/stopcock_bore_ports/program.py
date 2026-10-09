# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_stopcock_handle
def handle_vs_shut_port(key_reads, handle_reads, layout_reads, port_reads, bore_keys, shut_ports):
    """Worst angle between each stopcock handle and its shut port, plus port layouts confirmed."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def pick(v, opts):
        if v is None:
            return None
        s2 = ' '.join(str(v).lower().replace('-', ' ').split())
        if s2 in ('', 'none', 'n a', 'na', 'nil', 'empty', '?', '.'):
            return None
        for o in opts:
            if o in s2:
                return o
        return None
    def hour(v):
        d = ''.join(c for c in str(v) if c.isdigit())
        x = int(d) if d and len(d) <= 2 else None
        return x if x is not None and 1 <= x <= 12 else None
    want = [str(x) for x in lst(bore_keys)]
    shut_sides = [str(x).strip().lower() for x in lst(shut_ports)]
    got = align_by_printed_key([{'key': x, 'h': a, 's': b, 'p': c}
                                for x, a, b, c in zip(lst(key_reads), lst(handle_reads), lst(layout_reads), lst(port_reads))], want)
    worst, ok, notes = 0.0, 0, []
    for i, row in enumerate(got):
        r = row if isinstance(row, dict) else {}
        x = hour(r.get('h'))
        w = shut_sides[i] if i < len(shut_sides) else None
        t = 12.0 if w == 'up' else (float(hour(r.get('p'))) if hour(r.get('p')) else None)
        if x is None or t is None:
            return {'obs': 180.0, 'exp': 0.0, 'ports': ok,
                    'verdict': 'stopcock %s handle or sideways port not read'
                               % (want[i] if i < len(want) else i)}
        d = abs(((x % 12) * 30.0 - (t % 12) * 30.0 + 180.0) % 360.0 - 180.0)
        worst = d if d > worst else worst
        q = pick(r.get('s'), ['yes', 'no'])
        if q == 'yes':
            ok += 1
        notes.append('bore %s handle at %d oclock against the shut %s port standing at %g, '
                   'layout %r' % (want[i], x, w, t, q))
    return {'obs': worst, 'exp': 0.0, 'ports': ok, 'verdict': '; '.join(notes)}

# end of code_stopcock_handle
