# shared code: code_flag_set
def flagged_labels(labels, flags, truthy):
    """List the distinct labels whose flag answer equals the given value."""
    want = str(truthy).strip().lower()
    names = [''.join(str(a).lower().split()).strip('.,:') for a in ((labels or {}).get('answers') or [])]
    flagged = [str(b or '').strip().lower().strip('.') == want for b in ((flags or {}).get('answers') or [])]
    hits = [n for i, n in enumerate(names) if n and i < len(flagged) and flagged[i]]
    seq = ', '.join(sorted(set(hits)))
    return {'seq': seq, 'verdict': 'flagged references: %s' % (seq or 'none')}

# end of code_flag_set
