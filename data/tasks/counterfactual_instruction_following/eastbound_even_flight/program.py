# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_parity_map
def read_flight_parity(labels, vals):
    """Pair each lettered schedule row with whether its flight number is odd or even."""
    label_answers = (labels or {}).get('answers') or []
    value_answers = (vals or {}).get('answers') or []
    pairs = {}
    for a, b in zip(label_answers, value_answers):
        k = ''.join(c for c in str(a).lower() if c.isalpha())[-1:]
        d = ''.join(c for c in str(b) if c.isdigit())
        if k and d:
            pairs[k] = 'even' if int(d[-1]) % 2 == 0 else 'odd'
    canon = ' '.join('%s:%s' % (k, pairs[k]) for k in sorted(pairs))
    return {'canon': canon or 'nothing read',
            'verdict': 'read %d lettered rows: %s' % (len(pairs), canon or 'none')}

# end of code_parity_map

# shared code: code_side_map
def read_leg_sides(labels, vals):
    """Pair each lettered route segment with the side word read for it."""
    label_answers = (labels or {}).get('answers') or []
    value_answers = (vals or {}).get('answers') or []
    pairs = {}
    for a, b in zip(label_answers, value_answers):
        k = ''.join(c for c in str(a).lower() if c.isalpha())[-1:]
        v = ''.join(c for c in str(b).lower() if c.isalpha())
        if k and v:
            pairs[k] = v
    canon = ' '.join('%s:%s' % (k, pairs[k]) for k in sorted(pairs))
    return {'canon': canon or 'nothing read',
            'verdict': 'read %d lettered legs: %s' % (len(pairs), canon or 'none')}

# end of code_side_map
