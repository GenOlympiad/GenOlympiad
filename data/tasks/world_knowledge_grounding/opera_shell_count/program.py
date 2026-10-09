# code: helpers
from genolympiad.task_helpers import count_as_read, count_confirmed_cutouts
# end of helpers

# shared code: code_d8796ab24061
import re
def last_number(node):
    """The last number in the first answer, or a flag that no number was read."""
    a = (node or {}).get('answers') or [None]
    m = re.findall(r'\d{1,3}', str(a[0]))
    return {'n': int(m[-1]) if m else None, 'none': not m}

# end of code_d8796ab24061
