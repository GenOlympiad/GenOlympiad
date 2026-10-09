# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_row_key
def values_by_hole(node, keys):
    """Read each hole label and value pair and list the values in the reference hole order."""
    import re
    seen = {}
    for a in ((node or {}).get('answers') or []):
        m = re.search(r'([A-Za-z]+\s*\d+)\s*[=:]\s*([^\s,;]+)', str(a).strip())
        if not m:
            continue
        v = m.group(2).strip().strip('.').lower()
        v = ('%g' % float(v)) if re.match(r'^[+-]?\d+(\.\d+)?$', v) else v
        seen[m.group(1).replace(' ', '').lower()] = v
    return {'rows': [[seen.get(k, '')] for k in str(keys).split(',')], 'n': len(seen),
            'seen': 'table lines read: %s' % seen}

# end of code_row_key

# shared code: code_h2_pick
def second_hole_verdict_matches(node, grid):
    """Yes if the verdict printed for the second hole matches the reference grid."""
    rows = (node or {}).get('rows') or []
    got = str((rows[1] or [''])[0]).strip().lower() if len(rows) > 1 else ''
    want = str((grid[1] or [''])[0]).strip().lower() if len(grid or []) > 1 else ''
    ok = bool(want) and got == want
    return {'v': 'yes' if ok else 'no',
            'verdict': 'H2 printed %r, the convention actually commissioned wants %r' % (got, want)}

# end of code_h2_pick

# code: selfcons_code
def verdicts_agree_with_numbers(diameters, positions, verdicts_read):
    """Yes if all five printed verdicts follow from their printed size and position values."""
    import re
    col = lambda o: [str((r or [''])[0]).strip().lower() for r in ((o or {}).get('rows') or [])]
    d, p, v = col(diameters), col(positions), col(verdicts_read)
    num = lambda s: float(s) if re.match(r'^[+-]?\d+(\.\d+)?$', s) else None
    ok = 0
    for i in range(min(len(d), len(p), len(v))):
        a, b = num(d[i]), num(p[i])
        want = '' if (a is None or b is None) else ('pass' if b <= 0.2 + a - 8.0 + 1e-9 else 'fail')
        ok += 1 if (want and want == v[i]) else 0
    return {'v': 'yes' if (ok == 5 and len(v) == 5) else 'no', 'n': ok,
            'verdict': '%d of the five printed lines agree with the verdict printed beside them' % ok}

# end of selfcons_code
