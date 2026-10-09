# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: first_num_code
def first_number(node):
    """The first whole number in the first read answer, with the raw answer."""
    import re
    answers = list((node or {}).get('answers') or [])
    m = re.search(r'-?\d+', str(answers[0])) if answers else None
    return {'n': float(m.group(0)) if m else None, 'read': (answers[0] if answers else None)}

# end of first_num_code
