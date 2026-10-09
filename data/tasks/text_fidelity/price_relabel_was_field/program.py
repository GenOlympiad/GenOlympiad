# code: helpers
from genolympiad.task_helpers import sweep_holds_nothing_banned
# end of helpers

# shared code: code_kv
def map_product_to_price(keys, vals):
    """Key each ticket's read price to its product name, in name order."""
    products = [' '.join(str(k or '').lower().split()).strip(' .,:-') for k in (keys or {}).get('answers') or []]
    raw = [' '.join(str(v or '').lower().split()) for v in (vals or {}).get('answers') or []]
    rows = {}
    for i, k in enumerate(products):
        if not k or k == 'none' or k in rows:
            continue
        t = raw[i] if i < len(raw) else ''
        num = ''.join(c for c in t if c.isdigit() or c == '.')
        rows[k] = num if num else 'none'
    if not rows:
        return {'seq': 'none', 'refused': True,
                'verdict': 'no ticket came back with a product name to key on -> abstain'}
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'verdict': 'the tickets read back as %s' % seq}

# end of code_kv
