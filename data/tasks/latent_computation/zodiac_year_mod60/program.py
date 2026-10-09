# shared code: code_5af94135550e
def matches_reference(read, target):
    """1 if the read text equals the reference, ignoring case and outer spaces, else 0."""
    if not read:
        return 0.0
    return 1.0 if str(read).strip().lower() == str(target).strip().lower() else 0.0

# end of code_5af94135550e

# shared code: code_2a87a0f9b7b2
def normalise_answer(ans):
    """The answer lowercased, spaces removed and underscores turned into hyphens."""
    if ans is None or isinstance(ans, dict):
        return None
    return str(ans).strip().lower().replace(' ', '').replace('_','-')

# end of code_2a87a0f9b7b2
