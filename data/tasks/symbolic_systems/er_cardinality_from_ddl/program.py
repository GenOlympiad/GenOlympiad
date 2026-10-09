# shared code: code_labelset
def labelset(node):
    out = []
    for a in ((node or {}).get('answers') or []):
        t = ''.join(c for c in str(a).lower() if c.isalnum() or c in '.:')
        t = t.replace('..', '~').replace('.', '').replace('~', '..')
        if ':' in t and '..' in t:
            out.append(t)
    if not out:
        return {'seq': 'none', 'unreadable': True, 'refused': True,
                'verdict': 'no end label could be copied out'}
    out = sorted(out)
    return {'seq': '|'.join(out),
            'verdict': 'the line ends read ' + '|'.join(out)}

# end of code_labelset

# shared code: code_wordset
def wordset(node):
    """The sorted distinct words read from the cut-outs, joined into one string."""
    out = []
    for a in ((node or {}).get('answers') or []):
        t = ''.join(c for c in str(a).lower() if c.isalnum())
        if t:
            out.append(t)
    if not out:
        return {'seq': 'none', 'unreadable': True, 'refused': True,
                'verdict': 'nothing could be copied out of the cut-outs'}
    out = sorted(set(out))
    return {'seq': '|'.join(out), 'verdict': 'the cut-outs read ' + '|'.join(out)}

# end of code_wordset

# shared code: code_w9face_cardrun
def cardrun(node):
    raw = ''
    for a in ((node or {}).get('answers') or []):
        if str(a or '').strip():
            raw = str(a)
            break
    out = []
    for p in raw.replace(chr(10), ',').replace(';', ',').split(','):
        t = ''.join(c for c in p.lower() if c.isalnum() or c in '.:')
        t = t.replace('..', '~').replace('.', '').replace('~', '..')
        if ':' in t and '..' in t:
            out.append(t)
    if not out:
        return {'seq': 'none', 'refused': True, 'unreadable': True,
                'verdict': 'no end label could be copied off the sheet -> abstain'}
    out = sorted(out)
    return {'seq': '|'.join(out), 'n': len(out),
            'verdict': 'the line ends read ' + '|'.join(out)}

# end of code_w9face_cardrun

# shared code: code_w9fix_endmap
def end_labels_by_table(labels, tables):
    """Pair each line-end label with the table box it touches, joined into one string."""
    if not isinstance(labels, dict):
        labels = {}
    if not isinstance(tables, dict):
        tables = {}
    end_labels = []
    for a in (labels.get('answers') or []):
        t = ''.join(c for c in str(a or '').lower() if c.isalnum() or c in '.:')
        t = t.replace('..', '~').replace('.', '').replace('~', '..')
        end_labels.append(t if (':' in t and '..' in t) else '')
    table_names = [''.join(c for c in str(a or '').lower() if c.isalnum())
          for a in (tables.get('answers') or [])]
    by_end = {}
    for i, lab in enumerate(end_labels):
        table = table_names[i] if i < len(table_names) else ''
        if not lab or not table:
            continue
        rel, _, multiplicity = lab.partition(':')
        k = '%s:%s' % (rel, table)
        if k not in by_end:
            by_end[k] = multiplicity
    if not by_end:
        return {'seq': 'no reading', 'refused': True,
                'verdict': 'no line end gave both its label and the box it touches -> abstain'}
    seq = '|'.join('%s=%s' % (k, by_end[k]) for k in sorted(by_end))
    return {'seq': seq, 'n': len(by_end),
            'verdict': 'bound by the printed relation tag and box name: ' + seq}

# end of code_w9fix_endmap
