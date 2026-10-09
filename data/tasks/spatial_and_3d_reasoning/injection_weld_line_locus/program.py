# shared code: code_tag_num
def certified_tag_values(cert, txt):
    """List each certified read's tag with its last number, as a sorted schedule."""
    import re
    certified = [str(y).strip().lower().startswith('y') for y in ((cert or {}).get('answers') or [])]
    rows = []
    for i, t in enumerate(((txt or {}).get('answers') or [])):
        s = str(t).strip().lower()
        tag = (re.findall(r'\b([a-z]+\s?\d*)\b', s) or [''])[0]
        num = re.findall(r'\d+(?:\.\d+)?', s)
        if tag and num and (i >= len(certified) or certified[i]):
            rows.append('%s %g' % (tag.replace(' ', ''), float(num[-1])))
    seq = ', '.join(sorted(set(rows)))
    return {'seq': seq, 'n': len(rows), 'verdict': 'schedule read as: %s' % (seq or 'none')}

# end of code_tag_num

# shared code: code_both_yes
def count_confirmed_yes(cert, txt):
    """Count the confirmed cut-outs whose second question was also answered yes."""
    confirmed = [str(x).strip().lower().startswith('y') for x in ((cert or {}).get('answers') or [])]
    said_yes = [str(x).strip().lower().startswith('y') for x in ((txt or {}).get('answers') or [])]
    n = sum(1 for i in range(min(len(confirmed), len(said_yes))) if confirmed[i] and said_yes[i])
    n_confirmed = sum(1 for x in confirmed if x)
    return {'n': n, 'asked': n_confirmed,
            'verdict': '%d of the %d confirmed cut-outs also answered yes' % (n, n_confirmed)}

# end of code_both_yes
