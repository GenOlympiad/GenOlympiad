# shared code: code_tidy_string
def tidy_read_text(node):
    """The read text with spacing collapsed, and how many percent signs it holds."""
    raw = str(((node or {}).get('answers') or [''])[0])
    txt = ' '.join(raw.strip().split())
    return {'txt': txt or 'unreadable', 'n': txt.count('%'),
            'verdict': 'the cut-out was read back as %s' % (txt or 'nothing')}

# end of code_tidy_string
