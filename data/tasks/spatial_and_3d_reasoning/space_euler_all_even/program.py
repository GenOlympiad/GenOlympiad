# code: helpers
from genolympiad.task_helpers import count_listed_items, node_degrees
# end of helpers

# code: f_code
def full_or_raw_score(got, want, raw):
    """Full score when enough nodes reach degree four or more, else the raw score."""
    return 1.0 if int(got) >= int(want) else float(raw)

# end of f_code
