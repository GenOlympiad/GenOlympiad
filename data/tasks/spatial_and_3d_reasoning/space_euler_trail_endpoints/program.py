# code: helpers
from genolympiad.task_helpers import count_listed_items, node_degrees, node_degrees_with_colour
# end of helpers

# code: f_code
def odd_endpoint_score(n_marked, marked_are_odd, n_odd):
    """Score 1 when exactly two dots are marked and they are the odd degree dots."""
    if bool(marked_are_odd) and int(n_marked) == 2: return 1.0
    if int(n_marked) == 2: return 0.25
    return 0.0

# end of f_code
