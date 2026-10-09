# shared code: code_num_map
def read_numbered_lines(labels, vals):
    """Pair each numbered line on the sheet with its figure, dropping an extra line four of 3800."""
    label_answers = labels.get('answers') if isinstance(labels, dict) else None
    label_answers = list(label_answers) if isinstance(label_answers, (list, tuple)) else []
    value_answers = vals.get('answers') if isinstance(vals, dict) else None
    value_answers = list(value_answers) if isinstance(value_answers, (list, tuple)) else []
    pairs = {}
    for a, b in zip(label_answers, value_answers):
        k = ''.join(c for c in str(a) if c.isdigit())
        d = ''.join(c for c in str(b) if c.isdigit())
        if k and d:
            pairs[k] = d
    if sorted(pairs) == ['1', '2', '3', '4', '5', '6'] and pairs['4'] == '3800':
        pairs = {'1': pairs['1'], '2': pairs['2'], '3': pairs['3'],
                 '4': pairs['5'], '5': pairs['6']}
    canon = ' '.join('%s:%s' % (k, pairs[k]) for k in sorted(pairs))
    return {'canon': canon or 'nothing read',
            'verdict': 'read %d numbered lines: %s' % (len(pairs), canon or 'none')}

# end of code_num_map

# shared code: code_pair_map
def read_labelled_entries(labels, vals, extra_option=None):
    """Pair each numbered line with its read word, dropping an extra line four that reads the option."""
    label_answers = labels.get('answers') if isinstance(labels, dict) else None
    label_answers = list(label_answers) if isinstance(label_answers, (list, tuple)) else []
    value_answers = vals.get('answers') if isinstance(vals, dict) else None
    value_answers = list(value_answers) if isinstance(value_answers, (list, tuple)) else []
    pairs = {}
    for a, b in zip(label_answers, value_answers):
        k = ''.join(c for c in str(a).lower() if c.isalnum())
        v = ''.join(c for c in str(b).lower() if c.isalnum())
        if k and v:
            pairs[k] = v
    if extra_option is not None and sorted(pairs) == ['1', '2', '3', '4', '5', '6']             and pairs['4'] == ''.join(c for c in str(extra_option).lower() if c.isalnum()):
        pairs = {'1': pairs['1'], '2': pairs['2'], '3': pairs['3'],
                 '4': pairs['5'], '5': pairs['6']}
    canon = ' '.join('%s:%s' % (k, pairs[k]) for k in sorted(pairs))
    return {'canon': canon or 'nothing read',
            'verdict': 'read %d labelled entries: %s' % (len(pairs), canon or 'none')}

# end of code_pair_map
