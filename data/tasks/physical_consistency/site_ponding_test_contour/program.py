# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_ponding_set
def pad_number(a):
    import re
    m = re.search(r'p\s*(\d+)', str(a).lower())
    return m.group(1) if m else None

def pad_wet_matches(tag_reads, state_reads, wet_pads, n):
    """Share of pads whose wet or dry state matches the expected water surface."""
    rows = {}
    for a, b in zip((tag_reads or {}).get('answers') or [], (state_reads or {}).get('answers') or []):
        k = pad_number(a)
        if k:
            rows[k] = 'water' if 'water' in str(b).lower() else 'dry'
    wet = set(str(w) for w in (wet_pads or []))
    hits = sum(1 for k in rows if (rows[k] == 'water') == (k in wet))
    return {'rows': rows, 'hits': hits, 'frac': hits / float(n or 1),
            'note': '%d of the %d pads stand in the state the 23 mm water surface puts them in'
                    % (hits, n)}

# end of code_ponding_set
