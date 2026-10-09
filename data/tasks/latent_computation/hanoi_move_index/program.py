# code: helpers
from genolympiad.task_helpers import count_confirmed_disks, read_peg_stacks
# end of helpers

# code: plate_number_code

def plate_number(pl, confirms, numbers, reference):
    """The number on the first confirmed engraving plate, or -1 if none is readable."""
    import re

    def yes(a):
        return str(a).strip().lower().startswith('y')
    confirm_answers = (confirms or {}).get('answers') or []
    number_answers = (numbers or {}).get('answers') or []
    for i in range(min(len(confirm_answers), len(number_answers))):
        if not yes(confirm_answers[i]):
            continue
        m = re.search(r'\d+', str(number_answers[i]))
        if m:
            return {'n': int(m.group()), 'boxes': len(confirm_answers),
                    'verdict': 'the confirmed engraving plate reads %s' % m.group()}
    return {'n': -1, 'boxes': len(confirm_answers),
            'verdict': 'no confirmed engraving plate carried a readable number'}

# end of plate_number_code
