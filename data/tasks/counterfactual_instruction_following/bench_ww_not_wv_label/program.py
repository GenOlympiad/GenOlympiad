# code: helpers
from genolympiad.task_helpers import labelled_pairs
# end of helpers

# shared code: code_digit_map
def pair_fields_with_digits(labels, vals):
    """Pair each read field label with the digits read beside it, as sorted text."""
    label_reads = (labels or {}).get('answers') or []
    value_reads = (vals or {}).get('answers') or []
    pairs = {}
    for a, b in zip(label_reads, value_reads):
        k = ''.join(c for c in str(a).lower() if c.isalpha())
        d = ''.join(c for c in str(b) if c.isdigit())
        if k and d:
            pairs[k] = d
    canon = ' '.join('%s:%s' % (k, pairs[k]) for k in sorted(pairs))
    return {'canon': canon or 'nothing read',
            'verdict': 'read %d written fields: %s' % (len(pairs), canon or 'none')}

# end of code_digit_map
