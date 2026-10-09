# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: norm_code
def first_letters_upper(seq):
    """Keep the upper cased first character of each read entry, as one row."""
    return [[str(t).strip().upper()[:1] for t in seq]]

# end of norm_code
