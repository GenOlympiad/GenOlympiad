# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_moult_boundary
def moult_boundary_error(keys, fresh, grow, blocks, months, fresh_targets, grow_targets):
    """The worst miss, in feathers, between read and expected run-end ticks over the wings."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def tick(v):
        d = ''.join(c for c in str(v) if c.isdigit())
        return int(d) if d and 1 <= int(d) <= 9 else None
    printed_keys = [str(k).strip().upper() for k in lst(keys)]
    want = [str(m).strip().upper() for m in lst(months)]
    rows = align_by_printed_key([{'key': k, 'f': f, 'g': g, 'b': str(b).strip().lower()}
                                 for k, f, g, b in zip(printed_keys, lst(fresh), lst(grow), lst(blocks))],
                                want)
    fresh_list, grow_list = lst(fresh_targets), lst(grow_targets)
    worst, obs, exp, notes = -1.0, 0, 0, []
    for i, m in enumerate(want):
        r = rows[i] if i < len(rows) and isinstance(rows[i], dict) else {}
        run = 'togeth' in str(r.get('b') or '')
        for got, wanted, nm in ((tick(r.get('f')), fresh_list[i:i + 1], 'fresh run ends at'),
                                (tick(r.get('g')), grow_list[i:i + 1], 'growing run ends at')):
            w = int(wanted[0]) if wanted else 0
            miss = got is None or not run
            err, seen = (9.0, w + 9) if miss else (abs(got - w), got)
            notes.append('%s %s P%s, wants P%d' % (m, nm, 'none' if got is None else got, w))
            if err > worst:
                worst, obs, exp = err, seen, w
    return {'obs': obs, 'exp': exp, 'worst': worst,
            'verdict': '; '.join(notes) or 'no wing was read'}

# end of code_moult_boundary

# shared code: code_moult_score
def read_score_boxes(keys, cells, want):
    """Read the three moult scores written in each month's box, marking unread boxes."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    printed_keys = [str(k).strip().upper() for k in lst(keys)]
    want = [str(w).strip().upper() for w in lst(want)]
    rows = align_by_printed_key([{'key': k, 'v': str(v)} for k, v in zip(printed_keys, lst(cells))], want)
    got = []
    for i, w in enumerate(want):
        r = rows[i] if i < len(rows) and isinstance(rows[i], dict) else {}
        parts = [''.join(c for c in p if c.isdigit())
                 for p in str(r.get('v') or '').replace(';', ',').split(',')]
        parts = [p for p in parts if p]
        got.append('%s=%s' % (w, ','.join(parts) if len(parts) == 3 else 'unread'))
    return {'s': ';'.join(got), 'verdict': 'the score boxes read %s' % ('; '.join(got) or 'nothing')}

# end of code_moult_score
