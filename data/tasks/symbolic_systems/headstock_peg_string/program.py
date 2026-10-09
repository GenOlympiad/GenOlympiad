# code: peg_colours_code

def peg_colours(peg_boxes, peg_confirms, peg_colour_reads, reference):
    """Name the peg where each highlighted string colour ends, by side and height."""
    FAMILY = {'red': 'red', 'crimson': 'red', 'scarlet': 'red',
              'blue': 'blue', 'azure': 'blue', 'cyan': 'blue', 'turquoise': 'blue',
              'green': 'green', 'lime': 'green', 'emerald': 'green', 'teal': 'green',
              'magenta': 'magenta', 'pink': 'magenta', 'fuchsia': 'magenta',
              'purple': 'magenta', 'violet': 'magenta',
              'orange': 'orange', 'amber': 'orange',
              'yellow': 'yellow', 'gold': 'yellow',
              'grey': 'grey', 'gray': 'grey', 'silver': 'grey', 'black': 'grey',
              'white': 'grey'}

    def cx(b):
        return (float(b[1]) + float(b[3])) / 2.0

    def cy(b):
        return (float(b[0]) + float(b[2])) / 2.0

    def yes(a):
        return str(a).strip().lower().startswith('y')

    def fam(a):
        t = str(a or '').lower()
        for w in FAMILY:
            if w in t:
                return FAMILY[w]
        return ''

    geometry = (peg_boxes or {}).get('geometry') or []
    confirms = (peg_confirms or {}).get('answers') or []
    colour_reads = (peg_colour_reads or {}).get('answers') or []
    pegs = []
    for i in range(min(len(geometry), len(confirms))):
        if not yes(confirms[i]):
            continue
        pegs.append({'box': geometry[i], 'colour': fam(colour_reads[i] if i < len(colour_reads) else None)})

    res = {'n_pegs': len(pegs), 'p0': '', 'p1': ''}
    if len(pegs) != 6:
        res['verdict'] = ('%d tuning pegs were confirmed one at a time, but the headstock was '
                          'asked for six, so no peg can be named by where it sits' % len(pegs))
        return res

    by_x = sorted(pegs, key=lambda p: cx(p['box']))
    sides = {'left': sorted(by_x[:3], key=lambda p: cy(p['box'])),
             'right': sorted(by_x[3:], key=lambda p: cy(p['box']))}
    named = {}
    for side in ('left', 'right'):
        for k, row in enumerate(('top', 'middle', 'bottom')):
            named['%s-%s' % (row, side)] = sides[side][k]

    wanted = [str(c).strip().lower() for c in ((reference or {}).get('hl_colours') or [])]
    picked = []
    for c in wanted[:2]:
        want = FAMILY.get(c, c)
        hits = [n for n in named if named[n]['colour'] == want]
        picked.append(hits[0] if len(hits) == 1 else '')
    while len(picked) < 2:
        picked.append('')
    res['p0'], res['p1'] = picked[0], picked[1]
    res['found'] = dict((n, named[n]['colour']) for n in named)
    res['verdict'] = ('six tuning pegs were confirmed one at a time; the string ending on each '
                      'peg reads %s'
                      % ', '.join('%s: %s' % (n, named[n]['colour'] or 'not named')
                                  for n in sorted(named)))
    return res

# end of peg_colours_code

# code: score_code
POS=['top-left','middle-left','bottom-left','top-right','middle-right','bottom-right']
def norm(x):
    s=str(x).strip().lower().replace('_','-').replace(' ','')
    for p in POS:
        if p.replace('-','')==s: return p
    for p in POS:
        if p in str(x).strip().lower().replace('_','-'): return p
    return ''
def score(a0,a1,gt):
    got=[norm(a0),norm(a1)]; tg=gt['targets']
    ok=all(got[i]==tg[i] for i in range(2))
    return 1.0 if ok else 0.0

# end of score_code
