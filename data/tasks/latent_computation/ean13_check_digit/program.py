# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_539c8850d5db
def extract_13_digits(answer):
    """The 13 digit code in the answer, or None if there is none."""
    import re
    if answer is None or isinstance(answer, dict):
        return None
    digits = re.sub(r'[^0-9]', '', str(answer))
    if len(digits) == 13:
        return digits
    m = re.search(r'\d{13}', digits)
    return m.group(0) if m else None

# end of code_539c8850d5db

# code: pfx_code
def prefix_matches(read, prefix12):
    """1 if the first 12 digits read match the reference prefix, else 0."""
    if not read or len(read) != 13:
        return 0.0
    return 1.0 if read[:12] == str(prefix12) else 0.0

# end of pfx_code

# code: chk_code
def check_digit_matches(read, full13):
    """1 if the last digit read matches the reference check digit, else 0."""
    if not read or len(read) != 13:
        return 0.0
    return 1.0 if read[12] == str(full13)[12] else 0.0

# end of chk_code

# code: first12_code
def first_twelve_digits(node):
    """Join the first digit of each read box into a string of up to 12 digits."""
    import re
    a = list((node or {}).get('answers') or [])
    digits = [re.sub(r'\D', '', str(x))[:1] for x in a]
    digits = [d for d in digits if d]
    return {'s': ''.join(digits[:12]), 'n': len(digits)}

# end of first12_code
