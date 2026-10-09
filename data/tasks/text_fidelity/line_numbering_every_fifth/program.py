# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_fig_list
def margin_numbers(node):
    """The distinct margin figures read, in numeric order."""
    seen, vals = set(), []
    for raw in (node or {}).get('answers') or []:
        txt = ''.join(c for c in str(raw) if c.isdigit() or c == '.')
        if '.' in txt:
            txt = txt.rstrip('0').rstrip('.')
        if not txt or txt in seen:
            continue
        seen.add(txt)
        vals.append(txt)
    vals.sort(key=lambda s: (len(s.split('.')[0]), s))
    csv = ', '.join(vals)
    return {'csv': csv or 'no margin figure was read', 'n': len(vals),
            'verdict': 'the margin carries %d figures: %s' % (len(vals), csv or 'none')}

# end of code_fig_list

# shared code: code_two_reads
def two_margin_reads(a, b):
    """The first word read beside each of the two subsection openings."""
    def one(node):
        for raw in (node or {}).get('answers') or []:
            txt = str(raw).strip().lower()
            kept = ''.join(c if (c.isalnum()) else ' ' for c in txt).split()
            if kept:
                return kept[0]
        return 'nothing read'
    seq = '%s %s' % (one(a), one(b))
    return {'seq': seq,
            'verdict': 'the margin beside the two subsection openings reads %s' % seq}

# end of code_two_reads

# shared code: code_slipmap
def amendment_line_refs(keys, vals):
    """The line numbers that amendments 1 and 2 cite, keyed by their printed numbers."""
    import re
    ka = keys.get('answers') if isinstance(keys, dict) else None
    va = vals.get('answers') if isinstance(vals, dict) else None
    ka = list(ka) if isinstance(ka, (list, tuple)) else []
    va = list(va) if isinstance(va, (list, tuple)) else []
    by = {}
    for k, v in zip(ka, va):
        km = re.search(r'\d+', str(k))
        vm = re.search(r'\d+', str(v))
        if km and int(km.group()) not in by:
            by[int(km.group())] = vm.group() if vm else 'unread'
    seq = '|'.join(str(by.get(i, 'unread')) for i in (1, 2))
    return {'seq': seq, 'n': len(by),
            'verdict': 'amendment 1 cites %s and amendment 2 cites %s off their own printed numbers' % (by.get(1, 'unread'), by.get(2, 'unread'))}

# end of code_slipmap
