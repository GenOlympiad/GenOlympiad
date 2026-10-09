# code: dark_positions_code

def dark_positions(letter_boxes, letter_confirms, letter_states, reference):
    """List the places of the dark tube letters, counted from the left."""
    import re

    def cx(b):
        return (float(b[1]) + float(b[3])) / 2.0

    def yes(a):
        return str(a).strip().lower().startswith('y')

    def state(a):
        t = ' ' + re.sub(r'[^a-z]+', ' ', str(a).lower()).strip() + ' '
        if ' not glowing ' in t or ' not lit ' in t or ' not on ' in t:
            return 'dark'
        if ' dark ' in t or ' unlit ' in t or ' off ' in t or ' out ' in t:
            return 'dark'
        if ' glowing ' in t or ' glow ' in t or ' lit ' in t or ' on ' in t or ' bright ' in t:
            return 'lit'
        return None

    geo = (letter_boxes or {}).get('geometry') or []
    ok = (letter_confirms or {}).get('answers') or []
    val = (letter_states or {}).get('answers') or []
    letters = []
    for i in range(min(len(geo), len(ok))):
        if not yes(ok[i]):
            continue
        letters.append({'box': geo[i], 'state': state(val[i] if i < len(val) else None)})
    letters.sort(key=lambda d: cx(d['box']))
    want = int((reference or {}).get('n_letters') or 0)
    res = {'n': len(letters), 'want': want, 'asked': len(ok),
           'states': [d['state'] for d in letters]}
    if want and len(letters) != want:
        res['read'] = ('the sign does not carry one tube letter for every letter of the word the '
                       'prompt dictates, so no letter place can be counted off along it')
        res['verdict'] = ('%d tube letters were confirmed one at a time but the word the prompt '
                          'dictates has %d letters, so the row cannot be counted off'
                          % (len(letters), want))
        return res
    if any(d['state'] is None for d in letters):
        res['read'] = ('at least one tube letter could not be told apart as glowing or dark, so '
                       'no letter place can be named')
        res['verdict'] = ('%d tube letters were confirmed but at least one of them could not be '
                          'told apart as glowing or dark' % len(letters))
        return res
    dark = [i + 1 for i, d in enumerate(letters) if d['state'] == 'dark']
    res['dark'] = dark
    res['read'] = ','.join(str(p) for p in dark) if dark else '0'
    res['verdict'] = ('%d tube letters were confirmed one at a time; counting from the left, %s'
                      % (len(letters),
                         ('the dark ones are at places ' + ', '.join(str(p) for p in dark))
                         if dark else 'every one of them is glowing and none is dark'))
    return res

# end of dark_positions_code

# code: chk_code
def single_dark_place(ans, want):
    """1 if exactly one dark place was read and it is the expected one, else 0."""
    import re
    if ans is None or isinstance(ans, dict): return 0.0
    got = [int(x) for x in re.findall(r'\d+', str(ans))]
    seen = []
    for v in got:
        if v and v not in seen: seen.append(v)
    if len(seen) != 1: return 0.0
    return 1.0 if seen[0] == int(want) else 0.0

# end of chk_code
