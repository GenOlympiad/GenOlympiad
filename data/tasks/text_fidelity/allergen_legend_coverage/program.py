# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
import re
def norm(s): return ''.join(ch for ch in str(s).upper() if ch.isalnum() or ch.isspace())
def dish_codes_in_key(carrier, dishcodes, code, carriers, legend_keys):
    """1 if the dish is read and every allergen code it carries is defined in the key."""
    cN=norm(carrier)
    carrier_found=any(norm(c) and norm(c) in cN or cN in norm(c) for c in carriers)
    if not carrier_found: return 0.0
    keys=set(str(k).upper() for k in legend_keys)
    used=[ch for ch in str(dishcodes).upper() if ch.isalpha()]
    if not used: return 0.0
    for ch in used:
        if ch not in keys: return 0.0
    return 1.0

# end of law_code
