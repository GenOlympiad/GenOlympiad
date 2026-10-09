# shared code: code_date_words
def clean_date_line(node):
    """The read line as upper-case words, with leading zeros dropped from numbers."""
    answers = (node or {}).get('answers') or []
    raw = str(answers[0] if answers else '').upper()
    for ch in '.,-/':
        raw = raw.replace(ch, ' ')
    out = []
    for t in raw.split():
        out.append(str(int(t)) if t.isdigit() else t)
    return {'txt': ' '.join(out),
            'verdict': 'line read as %s' % (' '.join(out) or 'nothing')}

# end of code_date_words
