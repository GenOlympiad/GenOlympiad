# code: helpers
from genolympiad.task_helpers import count_listed_items, node_degrees
# end of helpers

# code: f_code
def uniform_degree_share(degrees, k):
    """Score the share of corners with the reference seam count, 0 at 80 percent up to 1 at all."""
    if not degrees: return 0.0
    n_match = sum(1 for d in degrees if int(d) == int(k))
    return round(max(0.0, min(1.0, (n_match / float(len(degrees)) - 0.80) / 0.20)), 4)

# end of f_code

# code: f_code_2
def degree_range_matches(min_degree, max_degree, k):
    """Score 1 if the fewest and most seams at any corner both equal the reference count."""
    return 1.0 if (int(min_degree) == int(k) and int(max_degree) == int(k)) else 0.0

# end of f_code_2
