# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_pairs
def paired_readings(first_reads, second_reads):
    """Join the first word of each first and second read into sorted pairs, such as 7 15."""
    a = [str(x).replace(',', '').strip().lower() for x in ((first_reads or {}).get('answers') or [])]
    b = [str(y).replace(',', '').strip().lower() for y in ((second_reads or {}).get('answers') or [])]
    rows = []
    for i, x in enumerate(a):
        if i < len(b) and x.split() and b[i].split():
            rows.append('%s %s' % (x.split()[0].strip('.:'), b[i].split()[0].strip('.:')))
    seq = ', '.join(sorted(set(rows)))
    return {'seq': seq, 'n': len(rows), 'verdict': 'read back as %s' % (seq or 'nothing')}

# end of code_pairs

# shared code: code_one_num
def digits_read(read):
    """The digits in the first answer at this place on the sheet, or unreadable."""
    raw = str((((read or {}).get('answers') or [''])[0]) or '')
    digits = ''.join(c for c in raw if c.isdigit())
    return {'txt': digits or 'unreadable',
            'verdict': 'the sheet reads %s at this place' % (digits or 'nothing')}

# end of code_one_num
