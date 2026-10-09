# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: m_code
def end_square_named(answer, target):
    """1 if the answer names the expected end square of the knight's tour, else 0."""
    import re
    if answer is None: return 0.0
    s = re.sub(r'[^a-h1-8]', '', str(answer).lower())
    return 1.0 if str(target).lower() in s else 0.0

# end of m_code
