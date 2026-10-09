# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
def letter_and_gpa_match(letter, gpa, want_letter, want_gpa, mark):
    """1 if the read letter grade and GPA both match the reference values, else 0."""
    import re
    letter_read = re.sub(r'[^A-Fa-f]', '', str(letter)).upper()[:1]
    if letter_read != str(want_letter).upper():
        return 0.0
    try:
        gpa_read = round(float(gpa), 2)
    except Exception:
        return 0.0
    if abs(gpa_read - round(float(want_gpa), 2)) > 0.005:
        return 0.0
    return 1.0

# end of law_code
