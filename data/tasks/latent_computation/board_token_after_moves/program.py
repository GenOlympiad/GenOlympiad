# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_182001ab8ec1
def square_matches(read, want_square):
    """Score 1 if the row letter and column digit read name the reference square."""
    if read is None or isinstance(read, dict):
        return 0.0
    text = str(read).strip().upper().replace(' ', '')
    letter = ''
    digit = ''
    for ch in text:
        if ch.isalpha() and not letter:
            letter = ch
        elif ch.isdigit() and not digit:
            digit = ch
    got = letter + digit
    return 1.0 if got == str(want_square).strip().upper() else 0.0

# end of code_182001ab8ec1
