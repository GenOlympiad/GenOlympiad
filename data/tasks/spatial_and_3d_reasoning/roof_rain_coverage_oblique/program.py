# shared code: code_name_set
def flagged_names(names, flags):
    """The sorted set of item names whose yes or no question came back yes."""
    names_read = [' '.join(str(a).strip().lower().split()).strip('.,:') 
          for a in ((names or {}).get('answers') or [])]
    flags_read = [str(b).strip().lower().startswith('y')
          for b in ((flags or {}).get('answers') or [])]
    hits = []
    for i, n in enumerate(names_read):
        if n and i < len(flags_read) and flags_read[i]:
            hits.append(n)
    seq = ', '.join(sorted(set(hits)))
    return {'seq': seq, 'n': len(set(hits)),
            'verdict': 'marked items read as: %s' % (seq or 'none')}

# end of code_name_set

# shared code: code_num_only
def certified_figure(confirm_reads, text_reads):
    """The most common figure read from cut-outs confirmed to show the key."""
    confirms = [str(y or '').strip().lower() for y in ((confirm_reads or {}).get('answers') or []) if str(y or '').strip()]
    if not confirms:
        return {'val': 'no reading', 'refused': True, 'verdict': 'the certifying question came back blank'}
    vals = []
    for i, tx in enumerate(((text_reads or {}).get('answers') or [])):
        if i < len(confirms) and confirms[i].startswith('y'):
            vals += ''.join(ch if (ch.isdigit() or ch == '.') else ' ' for ch in str(tx or '')).split()
    if not vals:
        return {'val': 'no certified figure', 'verdict': 'no cut-out carried the key beside a figure'}
    most_common = max(set(vals), key=vals.count)
    return {'val': most_common, 'verdict': 'figure read as %s from %d cut-out(s)' % (most_common, len(vals))}

# end of code_num_only
