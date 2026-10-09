# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_cuts_by_head
def read_cut_pairs(head, top, bot, keys):
    """Describe each cut as same or opposite arrow directions on its two faces, panel by heading."""
    def k(x):
        return ''.join(c for c in str(x).lower() if c.isalpha())
    def s(x):
        t = str(x).strip().lower()
        return 'up' if t.startswith('u') else ('down' if t.startswith('d') else '')
    heads = [k(x) for x in ((head or {}).get('answers') or [])]
    top_dirs = dict((heads[i], s(x)) for i, x in enumerate(((top or {}).get('answers') or [])) if i < len(heads))
    bottom_dirs = dict((heads[i], s(x)) for i, x in enumerate(((bot or {}).get('answers') or [])) if i < len(heads))
    panel_keys = [str(x) for x in (keys or [])] + ['', '', '']
    def cut(x, y):
        return 'unread' if not (x and y) else '%s %s' % ('opposite' if x != y else 'same', x)
    key = '%s|%s' % (cut(bottom_dirs.get(panel_keys[0], ''), top_dirs.get(panel_keys[1], '')), cut(bottom_dirs.get(panel_keys[1], ''), top_dirs.get(panel_keys[2], '')))
    return {'key': key, 'heads': ','.join(heads) or 'none',
            'verdict': 'the panels read back as %s and the two cuts came back %s'
                       % (','.join(heads) or 'none', key)}

# end of code_cuts_by_head

# shared code: code_same_figure
def cut_figures_match(head, top, bot, keys, want):
    """Whether both faces of the second cut show the same figure as the reference reaction."""
    def k(x):
        return ''.join(c for c in str(x).lower() if c.isalpha())
    def num(x):
        flat = ''.join(c if (c.isdigit() or c == '.') else ' ' for c in str(x).replace(',', ''))
        runs = [r.strip('.') for r in flat.split() if r.strip('.')]
        g = runs[-1] if runs else ''
        return (g.rstrip('0').rstrip('.') if '.' in g else g)
    heads = [k(x) for x in ((head or {}).get('answers') or [])]
    top_figures = dict((heads[i], num(x)) for i, x in enumerate(((top or {}).get('answers') or [])) if i < len(heads))
    bottom_figures = dict((heads[i], num(x)) for i, x in enumerate(((bot or {}).get('answers') or [])) if i < len(heads))
    panel_keys = [str(x) for x in (keys or [])] + ['', '', '']
    a, b = bottom_figures.get(panel_keys[1], ''), top_figures.get(panel_keys[2], '')
    ok = 'yes' if (a and a == b and a == str(want)) else 'no'
    return {'ok': ok, 'verdict': 'the stool underside reads %s and the pile cap top reads %s'
                                 % (a or 'nothing', b or 'nothing')}

# end of code_same_figure
