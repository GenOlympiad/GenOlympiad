# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_word_seq
def row_letters(reads):
    """The distinct row letters answered, sorted and joined."""
    letters = []
    for raw in (reads or {}).get('answers') or []:
        letter = ''.join(c for c in str(raw).lower() if c.isalpha())
        if letter:
            letters.append(letter)
    letters = sorted(set(letters))
    return {'seq': '|'.join(letters), 'n': len(letters),
            'verdict': 'the rows answered %s' % ('|'.join(letters) or 'nothing')}

# end of code_word_seq

# shared code: code_one_dec
def read_decimal(reads):
    """The digits and decimal point read from the first answer, or 'nothing'."""
    first_answer = str((((reads or {}).get('answers') or [''])[0]) or '')
    digits = ''.join(c for c in first_answer if c.isdigit() or c == '.').strip('.')
    return {'txt': digits or 'nothing',
            'verdict': 'the cut-out reads %s' % (digits or 'nothing')}

# end of code_one_dec
