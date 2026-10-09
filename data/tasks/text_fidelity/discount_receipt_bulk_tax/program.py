# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
def net_and_total_match(nt, tt, want_net, want_total):
    """1 if the read line net and grand total are within 0.02 of the reference, else 0."""
    try:
        a = float(nt); b = float(tt)
    except Exception:
        return 0.0
    if abs(a - float(want_net)) > 0.02:
        return 0.0
    if abs(b - float(want_total)) > 0.02:
        return 0.0
    return 1.0

# end of law_code
