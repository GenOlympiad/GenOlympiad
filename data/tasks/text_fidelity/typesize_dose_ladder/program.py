# shared code: code_size_map
def read_size_ladder(keys, vals, wanted):
    """List the margin values read for the wanted figure keys, in figure number order."""
    want = [w.strip() for w in str(wanted or '').split(',') if w.strip()]
    key_reads = [''.join(c for c in str(k or '') if c.isdigit()) for k in (keys or {}).get('answers') or []]
    value_reads = [' '.join(str(v or '').lower().split()).strip('.') for v in (vals or {}).get('answers') or []]
    rows = {}
    for i, k in enumerate(key_reads):
        if k in want and k not in rows:
            rows[k] = value_reads[i] if i < len(value_reads) and value_reads[i] else 'nothing'
    if not rows:
        return {'seq': 'none', 'refused': True,
                'verdict': 'no cut-out came back with a margin figure from the wanted set -> abstain'}
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows, key=lambda x: int(x)))
    return {'seq': seq, 'verdict': 'the ladder reads back as %s' % seq}

# end of code_size_map
