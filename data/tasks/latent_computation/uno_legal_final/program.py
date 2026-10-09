# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: top_ok_code
def top_discard_match(ans, top_colour, top_value):
    """Score 1 when the answer names the reference colour and value of the top discard."""
    import re
    s = re.sub(r'[^a-z0-9]', '', str(ans or '').lower())
    return 1.0 if (str(top_colour).lower() in s and str(top_value).lower() in s) else 0.0

# end of top_ok_code

# code: j_code
def combined_score(topf, handf):
    """Multiply the top discard score by the hand score."""
    return {'frac': float(topf) * float(handf)}

# end of j_code
