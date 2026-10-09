# shared code: code_row_parse
def read_row_heights(node):
    """Read each row's eye height and check the rise between rows grows from front to back."""
    import re
    heights = {}
    for a in (node or {}).get('answers') or []:
        m = re.search(r'[rR]\s*([1-5])\D*?(\d{3,4})', str(a))
        if m:
            heights['r' + m.group(1)] = int(m.group(2))
    chain = '|'.join('%s:%d' % (k, heights[k]) for k in sorted(heights))
    rises = [heights['r%d' % (i + 1)] - heights['r%d' % i] for i in range(1, 5) if 'r%d' % i in heights and 'r%d' % (i + 1) in heights]
    steepening = 'yes' if len(rises) == 4 and all(rises[j] < rises[j + 1] for j in range(3)) else 'no'
    return {'chain': chain, 'mono': steepening, 'verdict': '%d rows read; rises %s; steepening %s' % (len(heights), rises, steepening)}

# end of code_row_parse
