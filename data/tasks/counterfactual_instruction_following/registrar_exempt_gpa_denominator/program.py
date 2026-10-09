# shared code: code_two_columns
def credit_and_average_marks(credit_reads, average_reads):
    """Read tick or empty for each row in the credit and the average columns."""
    def col(node):
        v = []
        for a in (node or {}).get('answers') or []:
            s = str(a).strip().lower()
            v.append('tick' if s.startswith('t') else ('empty' if s.startswith('e') else '?'))
        return ','.join(v)
    a, b = col(credit_reads), col(average_reads)
    return {'s': a + '|' + b, 'verdict': 'the credit column reads %s and the average column reads %s' % (a, b)}

# end of code_two_columns

# code: pairn_code
def footnote_counts(a, b):
    """The first number in each of the two footnotes, joined as one text."""
    import re
    def one(node):
        d = re.findall(r'\d+', str(((node or {}).get('answers') or [''])[0]))
        return d[0] if d else '?'
    return {'s': one(a) + '/' + one(b), 'verdict': 'the footnotes count %s and %s courses' % (one(a), one(b))}

# end of pairn_code
