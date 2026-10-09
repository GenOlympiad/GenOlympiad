# shared code: code_pair_map
def pair_dates_with_words(labels, vals):
    """Pair each dated column's digits with the letters of its rule word, counting unread pairs."""
    date_answers = (labels or {}).get('answers') or []
    word_answers = (vals or {}).get('answers') or []
    if len(date_answers) != len(word_answers):
        return {'canon': 'box counts disagree %d vs %d' % (len(date_answers), len(word_answers)),
                'verdict': 'the two reads returned different box counts, nothing can be paired'}
    pairs = {}
    unread = 0
    for a, b in zip(date_answers, word_answers):
        k = ''.join(c for c in str(a) if c.isdigit())
        v = ''.join(c for c in str(b).lower() if c.isalpha())
        if k and v:
            pairs[k] = v
        else:
            unread += 1
    canon = ' '.join('%s:%s' % (k, pairs[k]) for k in sorted(pairs))
    if unread:
        canon = '%s unread:%d' % (canon or 'nothing read', unread)
    return {'canon': canon or 'nothing read',
            'verdict': 'read %d dated columns, %d unreadable: %s' % (len(pairs), unread, canon)}

# end of code_pair_map

# shared code: code_num_map
def pair_dates_with_figures(labels, vals):
    """Pair each dated column's digits with its daily figure, counting unread pairs."""
    date_answers = (labels or {}).get('answers') or []
    figure_answers = (vals or {}).get('answers') or []
    if len(date_answers) != len(figure_answers):
        return {'canon': 'box counts disagree %d vs %d' % (len(date_answers), len(figure_answers)),
                'verdict': 'the two reads returned different box counts, nothing can be paired'}
    pairs = {}
    unread = 0
    for a, b in zip(date_answers, figure_answers):
        k = ''.join(c for c in str(a) if c.isdigit())
        figure = ''.join(c for c in str(b) if c.isdigit())
        if k and figure:
            pairs[k] = figure
        else:
            unread += 1
    canon = ' '.join('%s:%s' % (k, pairs[k]) for k in sorted(pairs))
    if unread:
        canon = '%s unread:%d' % (canon or 'nothing read', unread)
    return {'canon': canon or 'nothing read',
            'verdict': 'read %d daily figures, %d unreadable: %s' % (len(pairs), unread, canon)}

# end of code_num_map

# shared code: code_digit_map
def pair_headings_with_figures(labels, vals):
    """Pair each heading's letters with its figure, counting unread pairs."""
    heading_answers = (labels or {}).get('answers') or []
    figure_answers = (vals or {}).get('answers') or []
    if len(heading_answers) != len(figure_answers):
        return {'canon': 'box counts disagree %d vs %d' % (len(heading_answers), len(figure_answers)),
                'verdict': 'the two reads returned different box counts, nothing can be paired'}
    pairs = {}
    unread = 0
    for a, b in zip(heading_answers, figure_answers):
        k = ''.join(c for c in str(a).lower() if c.isalpha())
        figure = ''.join(c for c in str(b) if c.isdigit())
        if k and figure:
            pairs[k] = figure
        else:
            unread += 1
    canon = ' '.join('%s:%s' % (k, pairs[k]) for k in sorted(pairs))
    if unread:
        canon = '%s unread:%d' % (canon or 'nothing read', unread)
    return {'canon': canon or 'nothing read',
            'verdict': 'read %d headed entries, %d unreadable: %s' % (len(pairs), unread, canon)}

# end of code_digit_map
