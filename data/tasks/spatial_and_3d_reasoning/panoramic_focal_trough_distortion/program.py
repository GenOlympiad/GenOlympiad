# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_width_verdict
def width_verdict(cert, txt):
    """Say whether each confirmed side's tooth width reads wider or narrower than the other."""
    import re
    confirmed = [str(y).strip().lower().startswith('y') for y in ((cert or {}).get('answers') or [])]
    got = {}
    for i, t in enumerate(((txt or {}).get('answers') or [])):
        s = str(t).strip().lower()
        n = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', s)]
        k = 'right' if 'right' in s else ('left' if 'left' in s else '')
        if k and len(n) > 1 and (i >= len(confirmed) or confirmed[i]):
            got[k] = 'wider' if n[0] > n[1] else 'narrower'
    seq = ', '.join('%s %s' % (k, got[k]) for k in sorted(got))
    return {'val': seq, 'verdict': 'width against the opposite side: %s' % (seq or 'none')}

# end of code_width_verdict

# shared code: code_height_verdict
def height_verdict(cert, txt):
    """Check that every confirmed tooth keeps the same crown height on both sides."""
    import re
    confirmed = [str(y).strip().lower().startswith('y') for y in ((cert or {}).get('answers') or [])]
    same = 0
    seen = 0
    for i, t in enumerate(((txt or {}).get('answers') or [])):
        n = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', str(t))]
        if len(n) > 1 and (i >= len(confirmed) or confirmed[i]):
            seen += 1
            same += 1 if abs(n[0] - n[1]) <= 0.5 else 0
    v = 'both crown heights match' if seen > 1 and same == seen else 'a crown height moved'
    return {'val': v, 'verdict': '%d of %d rows kept the crown height' % (same, seen)}

# end of code_height_verdict
