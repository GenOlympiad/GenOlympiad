# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_listed_items
# end of helpers

# code: ward_code
def slots_by_bed_number(slot_reads, number_reads, order):
    """Lay out the label read in each slot in the reference bed order, keyed by bed number."""
    keys = [str(x).strip().upper().replace(' ', '') for x in (number_reads or {}).get('answers') or []]
    keys = [k.zfill(2) if k.isdigit() else k for k in keys]
    values = [str(x).strip().upper() for x in (slot_reads or {}).get('answers') or []]
    seen = {}
    for k, v in zip(keys, values):
        seen.setdefault(k, v)
    line = [seen.get(b, '') for b in order]
    n_read = sum(1 for c in line if c)
    return {'grid': [line], 'n': n_read,
            'verdict': 'read %d of the %d slots by their stencilled bed number' % (n_read, len(order))}

# end of ward_code

# code: clash_code
def count_double_slots(slot_counts):
    """Count slots holding two or more patient labels, and whether none does."""
    counts = [str(x).strip() for x in (slot_counts or {}).get('answers') or []]
    n_over = sum(1 for v in counts if v.isdigit() and int(v) >= 2)
    total = sum(int(v) for v in counts if v.isdigit())
    return {'over': n_over, 'tot': total, 'n': len(counts),
            'clean': 'yes' if n_over == 0 and total > 0 else 'no',
            'verdict': '%d of the %d slots hold two headcards; %d headcards counted in all'
                       % (n_over, len(counts), total)}

# end of clash_code
