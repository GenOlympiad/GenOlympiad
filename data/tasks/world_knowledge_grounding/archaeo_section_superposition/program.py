# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: reg_match_code
def count_register_matches(keys, vals, want):
    """Count the register rows that name the deposit the reference cut depth reaches."""
    wanted = dict(p.split('=') for p in str(want).split('|') if p.count('=') == 1)
    keys_read = [str(a).strip().lstrip('0') or '0' for a in ((keys or {}).get('answers') or [])]
    values_read = [str(a).strip().lower() for a in ((vals or {}).get('answers') or [])]
    n = 0
    for k, s in zip(keys_read, values_read):
        t = str(wanted.get(k, '')).strip().lower()
        if t and t in s:
            n += 1
    return {'n': n, 'asked': len(values_read), 'verdict': '%d of the %d register rows name the deposit the recorded depth actually reaches' % (n, len(values_read))}

# end of reg_match_code

# code: edge_fate_code
def count_edge_matches(a, b, c, want):
    """Count the deposit lines that behave at the pit edge as the reference requires."""
    wanted = [p.strip().lower() for p in str(want).split('|')]
    got = []
    for node in (a, b, c):
        ans = [str(x).strip().lower() for x in ((node or {}).get('answers') or [])]
        got.append(ans[0] if ans else '')
    n = sum(1 for t, s in zip(wanted, got) if t and t in s)
    return {'n': n, 'asked': len(wanted), 'verdict': '%d of the %d deposit lines behave at the pit edge as the recorded depth requires' % (n, len(wanted))}

# end of edge_fate_code
