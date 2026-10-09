# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_pair_set
def certified_egg_attitudes(cert, keys, vals):
    """Pair each certified egg's date with its read attitude, dropping incomplete reads."""
    certified = [str(y).strip().lower().startswith('y') for y in ((cert or {}).get('answers') or [])]
    dates = [''.join(str(a).lower().split()).strip('.,:') for a in ((keys or {}).get('answers') or [])]
    attitudes = [''.join(str(b).lower().split()).strip('.,:') for b in ((vals or {}).get('answers') or [])]
    rows, dropped = [], 0
    for i, k in enumerate(dates):
        if not k or i >= len(attitudes) or not attitudes[i] or (i < len(certified) and not certified[i]):
            dropped += 1
            continue
        rows.append('%s %s' % (k, attitudes[i]))
    seq = ', '.join(sorted(set(rows)))
    if not rows:
        return {'seq': 'no certified egg reading', 'n': 0, 'dropped': dropped,
                'verdict': 'not one egg in the glass gave a certified date and attitude together'}
    return {'seq': seq, 'n': len(set(rows)), 'dropped': dropped,
            'verdict': 'read as: %s (%d cut-outs dropped for want of a certificate, a date or '
                       'an attitude)' % (seq, dropped)}

# end of code_pair_set

# shared code: code_pair_num
def certified_aircell_depths(cert, keys, vals):
    """Pair each certified frame's date with its read air pocket depth, dropping incomplete reads."""
    import re
    certified = [str(y).strip().lower().startswith('y') for y in ((cert or {}).get('answers') or [])]
    dates = [''.join(str(a).lower().split()).strip('.,:') for a in ((keys or {}).get('answers') or [])]
    rows, dropped = [], 0
    for i, t in enumerate(((vals or {}).get('answers') or [])):
        if i < len(certified) and not certified[i]:
            dropped += 1
            continue
        m = re.search(r'\d+(?:\.\d+)?', str(t))
        if not m or i >= len(dates) or not dates[i]:
            dropped += 1
            continue
        depth_text = m.group(0)
        if '.' in depth_text:
            depth_text = depth_text.rstrip('0').rstrip('.')
        rows.append('%s %s' % (dates[i], depth_text))
    seq = ', '.join(sorted(set(rows)))
    if not rows:
        return {'seq': 'no certified cell reading', 'n': 0, 'dropped': dropped,
                'verdict': 'not one candling frame gave a certified date and depth together'}
    return {'seq': seq, 'n': len(set(rows)), 'dropped': dropped,
            'verdict': 'rows read as: %s (%d cut-outs dropped for want of a certificate, a '
                       'date or a figure)' % (seq, dropped)}

# end of code_pair_num
