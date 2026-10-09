# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_pair_map
def pair_lines_with_values(labels, vals):
    """Pair each read line number with its read value, as sorted key:value text."""
    label_reads = (labels or {}).get('answers') or []
    value_reads = (vals or {}).get('answers') or []
    pairs = {}
    for a, b in zip(label_reads, value_reads):
        k = ''.join(c for c in str(a).lower() if c.isalnum())
        v = ''.join(c for c in str(b).lower() if c.isalnum())
        if k and v:
            pairs[k] = v
    canon = ' '.join('%s:%s' % (k, pairs[k]) for k in sorted(pairs))
    return {'canon': canon or 'nothing read',
            'verdict': 'read %d numbered lines: %s' % (len(pairs), canon or 'none')}

# end of code_pair_map
