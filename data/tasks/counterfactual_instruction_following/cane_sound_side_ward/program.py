# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_keyjoin
def values_by_bed_key(keys, vals, order):
    """Bind each read value to its printed bed key, listed in the reference bed order."""
    key_reads = (keys or {}).get('answers') or []
    value_reads = (vals or {}).get('answers') or []
    by = {}
    for k, v in zip(key_reads, value_reads):
        kk = ''.join(c for c in str(k).lower() if c.isalnum())
        vv = ' '.join(str(v).lower().split())
        vv = ''.join(c for c in vv if c.isalnum() or c in ' .-').strip()
        if kk and kk not in by:
            by[kk] = vv or 'blank'
    want = [''.join(c for c in w.lower() if c.isalnum()) for w in str(order).split('|')]
    got = [by.get(w, 'unread') for w in want]
    if all(g == 'unread' for g in got):
        return {'seq': 'no reading', 'refused': True,
                'verdict': 'not one cut-out printed a key belonging to this run -> abstain'}
    return {'seq': '|'.join(got), 'n': len(by),
            'verdict': 'bound by printed key: ' + '; '.join('%s -> %s' % (w, g)
                       for w, g in zip(want, got))}

# end of code_keyjoin
