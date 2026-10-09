# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
def change_and_net_match(chg, net, want_chg, want_net, want_takings):
    """1 if the read change and net cash match the reference and the takings, else 0."""
    try:
        c = float(chg); n = float(net)
    except Exception:
        return 0.0
    if abs(c - float(want_chg)) > 0.02:
        return 0.0
    if abs(n - float(want_net)) > 0.02:
        return 0.0
    if abs(float(want_net) - float(want_takings)) > 0.02:
        return 0.0
    return 1.0

# end of law_code
