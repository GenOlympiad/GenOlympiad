# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_row_gap
def row_sums_and_blanks(name_reads, value_reads):
    """Per row name, the sum of the numbers read and the count of blank entries."""
    g = lambda x: [str(s).strip() for s in ((x or {}).get('answers') or [])]
    names, values, rows = g(name_reads), g(value_reads), {}
    for i, k in enumerate(names):
        key = k.strip().upper()
        if not key or i >= len(values) or key in rows: continue
        parts = [p.strip().upper() for p in values[i].replace(';', ',').split(',')]
        nums = [float(p) for p in parts if p.replace('.', '', 1).isdigit()]
        rows[key] = [sum(nums), sum(1 for p in parts if p in ('EMPTY', 'NONE', 'BLANK', ''))]
    seq = ';'.join('%s=%d' % (k, round(rows[k][0])) for k in sorted(rows))
    blank_seq = ';'.join('%s=%d' % (k, rows[k][1]) for k in sorted(rows))
    return {'seq': seq, 'blk': blank_seq, 'n': len(rows)}

# end of code_row_gap
