# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# code: allequal_code
import re
def all_counts_equal(node):
    """Score 1 when the pouch counts of at least two read boxes are all equal."""
    answers = (node or {}).get('answers') or []
    nums = []
    for a in answers:
        hits = re.findall(r'-?\d+', str(a if a is not None else ''))
        if hits:
            nums.append(int(hits[-1]))
    if len(nums) < 2:
        return {'frac': 0.0, 'no_read': True, 'counts': nums,
                'verdict': 'fewer than two boxes could be read per-box'}
    same = (len(set(nums)) == 1)
    return {'frac': 1.0 if same else 0.0, 'no_read': False, 'counts': nums,
            'verdict': 'per-box pouch counts %s -> %s' % (nums, 'all equal' if same else 'unequal')}

# end of allequal_code
