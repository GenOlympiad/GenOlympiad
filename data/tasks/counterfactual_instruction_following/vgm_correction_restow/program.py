# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_pair_map
def read_stow_pairs(tier_reads, owner_reads):
    """Pair each tier label read with the owner code read beside it, sorted."""
    la = (tier_reads or {}).get('answers') or []
    va = (owner_reads or {}).get('answers') or []
    pairs = {}
    for a, b in zip(la, va):
        k = ''.join(c for c in str(a).lower() if c.isalnum())
        v = ''.join(c for c in str(b).lower() if c.isalnum())
        if k and v:
            pairs[k] = v
    canon = ' '.join('%s:%s' % (k, pairs[k]) for k in sorted(pairs))
    return {'canon': canon or 'nothing read',
            'verdict': 'read %d labelled cells: %s' % (len(pairs), canon or 'none')}

# end of code_pair_map

# shared code: code_num_map
def read_tier_weights(tier_reads, mass_reads):
    """Pair each tier number read with the mass read beside it, sorted."""
    la = (tier_reads or {}).get('answers') or []
    va = (mass_reads or {}).get('answers') or []
    pairs = {}
    for a, b in zip(la, va):
        k = ''.join(c for c in str(a) if c.isdigit())
        d = ''.join(c for c in str(b) if c.isdigit())
        if k and d:
            pairs[k] = d
    canon = ' '.join('%s:%s' % (k, pairs[k]) for k in sorted(pairs))
    return {'canon': canon or 'nothing read',
            'verdict': 'read %d tiers: %s' % (len(pairs), canon or 'none')}

# end of code_num_map
