# shared code: code_onetxt
def first_reading_text(node):
    """The first non-empty reading of the cut-out, lower case with punctuation removed."""
    for raw in (node or {}).get('answers') or []:
        t = ' '.join(str(raw or '').lower().split())
        t = ''.join(c for c in t if c.isalnum() or c == ' ')
        t = ' '.join(t.split())
        if t:
            return {'v': t, 'verdict': 'the cut-out reads: %s' % t}
    return {'v': 'no reading', 'refused': True,
            'verdict': 'no words came back out of the cut-out -> abstain'}

# end of code_onetxt

# shared code: code_w9face_num
def sum_counts(*nodes):
    """The total of the counts read from the cut-outs, as digits or number words."""
    import re
    words = {'none': 0, 'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
             'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11,
             'twelve': 12}
    total, n_read = 0, 0
    for nd in nodes:
        for a in ((nd or {}).get('answers') or []):
            s = str(a or '').lower().replace(',', '')
            m = re.search(r'\d+', s)
            hit = int(m.group(0)) if m else next(
                (v for w, v in words.items() if re.search(r'\b%s\b' % w, s)), None)
            if hit is not None:
                total += hit
                n_read += 1
    if not n_read:
        return {'n': -1, 'refused': True, 'unreadable': True,
                'verdict': 'no count came back out of the cut-outs -> abstain'}
    return {'n': total, 'asked': n_read,
            'verdict': 'the cut-outs were counted and came to %d' % total}

# end of code_w9face_num

# code: lettersonly_code
def lettersonly(node):
    """The first non-empty reading of the comb with only letters and digits kept."""
    for raw in ((node or {}).get('answers') or []):
        t = ''.join(c for c in str(raw or '').lower() if c.isalnum())
        if t:
            return {'v': t, 'verdict': 'the comb reads: %s' % t}
    return {'v': 'no reading', 'refused': True, 'unreadable': True,
            'verdict': 'nothing came back out of the cut-out -> abstain'}

# end of lettersonly_code
