# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# code: verdict_code
import re

def num(a):
    m = re.findall(r'-?\d+', str(a))
    return int(m[-1]) if m else None

def score_plan_elevation(plan_reads, elev_reads, plan_want, elev_want, names, pinned):
    """Score plan and elevation counts, and whether only the pinned item disagrees."""
    plan_counts = [num(x) for x in plan_reads]
    elev_counts = [num(x) for x in elev_reads]
    if any(v is None for v in plan_counts + elev_counts):
        return {'frac': 0.0, 'unreadable': True, 'plan': plan_counts, 'elev': elev_counts}
    plan_expected = [int(v) for v in plan_want]
    elev_expected = [int(v) for v in elev_want]
    hits = sum(1 for a, b in zip(plan_counts, plan_expected) if a == b) + \
           sum(1 for a, b in zip(elev_counts, elev_expected) if a == b)
    value_frac = hits / float(len(plan_expected) + len(elev_expected))
    mismatch = sorted(str(names[i]) for i in range(len(plan_counts)) if plan_counts[i] != elev_counts[i])
    struct_ok = 1.0 if mismatch == [str(pinned)] else 0.0
    if len(mismatch) == 0:
        pathology = 'panels_forced_into_full_agreement'
    elif len(mismatch) >= 2:
        pathology = 'panels_drawn_independently'
    elif struct_ok == 0.0:
        pathology = 'wrong_single_item_disagrees'
    else:
        pathology = ''
    return {'frac': round(0.4 * value_frac + 0.6 * struct_ok, 4),
            'plan': plan_counts, 'elev': elev_counts, 'plan_expected': plan_expected, 'elev_expected': elev_expected,
            'mismatch_set': mismatch, 'mismatch_n': len(mismatch),
            'pinned': str(pinned), 'pathology': pathology}

# end of verdict_code

# code: seen_code
def any_box_found(node):
    """Give 1 if any box was found, else 0."""
    return 1.0 if ((node or {}).get('geometry') or []) else 0.0

# end of seen_code
