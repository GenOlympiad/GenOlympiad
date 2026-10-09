# code: ex_code
def extract_letters(answer):
    """Keep only the capital letters of the answer, or None if there are none."""
    import re
    if answer is None or isinstance(answer, dict):
        return None
    return re.sub(r'[^A-Z]', '', str(answer).strip().upper()) or None

# end of ex_code

# code: chk_code
def cipher_matches(read, want):
    """1 if the read letters equal the expected cipher text, else 0."""
    if not read:
        return 0.0
    return 1.0 if read == str(want) else 0.0

# end of chk_code
