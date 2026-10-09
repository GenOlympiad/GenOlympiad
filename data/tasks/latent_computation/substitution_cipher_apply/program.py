# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: up_code
def first_letters_upper(seq):
    """Keep the first character of each read, in upper case."""
    return [[str(r[0]).strip().upper()[:1]] for r in seq]

# end of up_code
