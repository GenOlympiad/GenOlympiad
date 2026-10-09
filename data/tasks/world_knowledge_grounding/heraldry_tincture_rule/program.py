# code: helpers
from genolympiad.task_helpers import (
    count_confirmed_cutouts, count_listed_items, paint_cells_by_fraction, plan_grid_from_read_count)
# end of helpers

# shared code: code_shield_tinctures
def check_shield_tinctures(field_read, charge_read, metals, colours):
    """Count shields with metal on metal or colour on colour, and shields using listed tinctures."""
    field_answers = ((field_read or {}).get('answers') or [])
    charge_answers = ((charge_read or {}).get('answers') or [])
    def cls(x):
        w = str(x).strip().lower()
        return 'M' if w in metals else ('C' if w in colours else '?')
    pairs = [(cls(a), cls(b)) for a, b in zip(field_answers, charge_answers)]
    n_bad = sum(1 for p in pairs if p[0] == p[1] and p[0] in ('M', 'C'))
    n_listed = sum(1 for p in pairs if '?' not in p)
    return {'n_bad': n_bad, 'n_listed': n_listed, 'n': len(pairs), 'pairs': pairs,
            'verdict': '%d of %d shields lay like class over like class; %d shields use only the heraldic tinctures' % (n_bad, len(pairs), n_listed)}

# end of code_shield_tinctures
