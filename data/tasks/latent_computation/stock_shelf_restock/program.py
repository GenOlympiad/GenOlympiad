# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: tallest_slot_code
def tallest_slot(cells):
    """The position, counted from one, of the tallest slot value read."""
    values = ((cells or {}).get('values') or [[]])[0]
    nums = []
    for v in values:
        try:
            nums.append(float(v))
        except (TypeError, ValueError):
            return ''
    if not nums:
        return ''
    return str(nums.index(max(nums)) + 1)

# end of tallest_slot_code
