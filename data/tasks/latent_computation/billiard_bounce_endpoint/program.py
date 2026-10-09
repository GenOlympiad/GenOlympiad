# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: ex_code
def corner_code(answer):
    """Short code of the table corner named in the answer, such as TL."""
    import re
    if answer is None or isinstance(answer, dict):
        return None
    text = re.sub(r'[^a-z]', '', str(answer).strip().lower())
    corner_codes = {'topleft':'TL','topright':'TR','bottomleft':'BL','bottomright':'BR'}
    for k, v in corner_codes.items():
        if k in text:
            return v
    return None

# end of ex_code

# code: bad_code
def read_failed(reading):
    """True if the corner answer is missing or came back as a refusal."""
    return isinstance(reading, dict) or reading is None

# end of bad_code
