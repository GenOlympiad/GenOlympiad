# shared code: code_span
def words_around_mark(before, after):
    """The words on either side of the upside-down mark on this line."""
    def one(node):
        raw = str(((node or {}).get('answers') or [''])[0])
        return ''.join(c for c in raw.strip().lower() if c.isalpha())
    b, a = one(before), one(after)
    if not b or not a:
        return {'unreadable': True, 'txt': '',
                'verdict': 'a word beside the upside-down mark did not come back -> honest refusal'}
    if b == 'none' or a == 'none':
        return {'unreadable': False, 'txt': 'no mark on this line',
                'verdict': 'the reader found no upside-down mark on this line, or none with a word standing before it'}
    return {'unreadable': False, 'txt': b + '>' + a,
            'verdict': 'the upside-down mark on this line stands between %s and %s' % (b, a)}

# end of code_span

# code: allmarked_code
def all_lines_marked(v, want):
    """Whether every line carries an upside-down opening mark."""
    seen = [str(x).strip().lower()[:1] for x in (v or {}).get('answers') or []]
    yes = sum(1 for x in seen if x == 'y')
    if len(seen) != int(want):
        return {'unreadable': True, 'ok': 'no', 'verdict': 'the sweep produced %d lines where %d were wanted -> honest refusal' % (len(seen), int(want))}
    return {'unreadable': False, 'ok': 'yes' if yes == int(want) else 'no', 'verdict': '%d of the %d lines carry an upside-down opening mark' % (yes, len(seen))}

# end of allmarked_code
