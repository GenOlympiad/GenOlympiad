# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_5af94135550e
def matches_reference(read, target):
    """1.0 if the weekday read equals the reference weekday, else 0.0."""
    if not read:
        return 0.0
    return 1.0 if str(read).strip().lower() == str(target).strip().lower() else 0.0

# end of code_5af94135550e

# shared code: code_a4a97af85a75
def read_weekday(ans):
    """The full weekday name found in the answer, or None if there is none."""
    if ans is None or isinstance(ans, dict):
        return None
    s = str(ans).strip().lower()
    days = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday']
    abbreviations = {'sun':'sunday','mon':'monday','tue':'tuesday','tues':'tuesday','wed':'wednesday',
            'thu':'thursday','thur':'thursday','thurs':'thursday','fri':'friday','sat':'saturday'}
    for dd in days:
        if dd in s:
            return dd
    import re
    for w in re.findall(r'[a-z]+', s):
        if w in abbreviations:
            return abbreviations[w]
    return None

# end of code_a4a97af85a75
