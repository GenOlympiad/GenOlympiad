# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: prog_code
def sampled_numbers(node):
    """The distinct voucher numbers read from the sample column, in ascending order."""
    texts = [str(x) for x in (node or {}).get('answers') or []]
    numbers = []
    for t in texts:
        digits = ''.join(c for c in t if c.isdigit())
        if digits:
            numbers.append(int(digits[-4:]) if len(digits) > 4 else int(digits))
    s = '|'.join(str(v) for v in sorted(set(numbers)))
    return {'seq': s, 'n': len(numbers),
            'verdict': 'sample column read back as %s' % (s or 'nothing')}

# end of prog_code

# code: pulled_code
def pulled_voucher_hits(node):
    """Count the expected sample numbers found on the pulled vouchers, less any strays."""
    texts = [str(x) for x in (node or {}).get('answers') or []]
    found = set()
    for t in texts:
        digits = ''.join(c for c in t if c.isdigit())
        if digits:
            found.add(int(digits[-4:]) if len(digits) > 4 else int(digits))
    expected = set([4319, 4719, 5119, 5519, 5919, 6319, 6719, 7119])
    n, stray = len(expected & found), len(found - expected)
    v = n - stray if n > stray else 0
    return {'n': v, 'hits': n, 'stray': stray,
            'verdict': '%d of the 8 sampled numbers found on the pulled vouchers, %d stray' % (n, stray)}

# end of pulled_code
