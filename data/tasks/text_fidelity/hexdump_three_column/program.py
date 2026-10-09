# shared code: code_row_text
def text_column_by_offset(keys, vals, want):
    """Key each row's text column to its offset and compare with the expected text."""
    offsets = [''.join(c for c in str(k or '').lower() if c in '0123456789abcdef')
          for k in (keys or {}).get('answers') or []]
    texts = [str(v or '').strip() for v in (vals or {}).get('answers') or []]
    rows = {}
    for i, k in enumerate(offsets):
        if k and k not in rows:
            rows[k] = texts[i] if i < len(texts) and texts[i] else 'nothing'
    if not rows:
        return {'seq': 'none', 'tag': 'no', 'refused': True,
                'verdict': 'no row cut-out came back with an offset to key on -> abstain'}
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    tag = 'yes' if seq == str(want) else 'no'
    return {'seq': seq, 'tag': tag,
            'verdict': 'the text column reads back as %s; the bytes require %s'
                       % (seq, want)}

# end of code_row_text

# code: offs_code
def offset_column(node):
    """The distinct hex offsets read from the left column, sorted."""
    seen = []
    for raw in (node or {}).get('answers') or []:
        t = ''.join(c for c in str(raw or '').lower() if c in '0123456789abcdef')
        if t and t not in seen:
            seen.append(t)
    if not seen:
        return {'seq': 'none', 'refused': True,
                'verdict': 'no row cut-out came back with a left-hand block -> abstain'}
    seen.sort()
    return {'seq': ','.join(seen), 'verdict': 'the left column reads %s' % ','.join(seen)}

# end of offs_code
