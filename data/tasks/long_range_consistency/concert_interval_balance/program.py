# shared code: code_nums
def sorted_figures(node):
    """All figures read back, trailing zeros dropped, sorted by size."""
    values = []
    for raw in (node or {}).get('answers') or []:
        txt = ''.join(c for c in str(raw) if c.isdigit() or c == '.').strip('.')
        if txt and txt.count('.') < 2:
            values.append(txt.rstrip('0').rstrip('.') if '.' in txt else txt)
    values.sort(key=lambda t: (len(t.split('.')[0]), t))
    seq = '|'.join(values)
    return {'seq': seq, 'n': len(values),
            'verdict': 'the figures read back as %s' % (seq or 'nothing')}

# end of code_nums

# shared code: code_one_dec
def read_decimal(node):
    """The decimal figure read from the cut-out."""
    raw = str((((node or {}).get('answers') or [''])[0]) or '')
    txt = ''.join(c for c in raw if c.isdigit() or c == '.').strip('.')
    return {'txt': txt or 'nothing',
            'verdict': 'the cut-out reads %s' % (txt or 'nothing')}

# end of code_one_dec

# shared code: code_one_clock
def clock_time(node):
    """The clock time read from the cut-out, digits and colons only."""
    raw = str((((node or {}).get('answers') or [''])[0]) or '')
    txt = ''.join(c for c in raw if c.isdigit() or c == ':').strip(':')
    return {'txt': txt or 'nothing',
            'verdict': 'the cut-out reads %s' % (txt or 'nothing')}

# end of code_one_clock
