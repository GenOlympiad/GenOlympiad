# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_edges
def edges(wh, wl, eh, el, want_w, want_e):
    def head(node):
        s = ''.join(ch for ch in str((((node or {}).get('answers') or [''])[0])) if ch.isalnum())
        return s.upper()
    def names(node):
        out = []
        for a in ((node or {}).get('answers') or []):
            for tok in str(a).upper().replace(',', ' ').split():
                t = ''.join(ch for ch in tok if ch.isalnum() or ch == '-')
                if t.count('-') == 1 and all(p for p in t.split('-')):
                    out.append(t)
        return out
    hw, he = head(wh), head(eh)
    nw, ne = names(wl), names(el)
    placed = ('123' in hw or '12-3' in hw) and ('124' in he or '12-4' in he)
    w_ok = str(want_w) in nw
    e_ok = str(want_e) in ne
    ok = 'yes' if (placed and w_ok and e_ok) else 'no'
    return {'v': ok, 'placed': 'yes' if placed else 'no',
            'verdict': 'headings read %s and %s; west table lists %s; east table lists %s'
                       % (hw or 'nothing', he or 'nothing',
                          '|'.join(nw) or 'nothing', '|'.join(ne) or 'nothing')}

# end of code_edges

# shared code: code_ends
def ends(up_node, low_node, north, south):
    def one(node):
        s = str((((node or {}).get('answers') or [''])[0])).upper()
        return ''.join(ch for ch in s if ch.isalnum())
    u, d = one(up_node), one(low_node)
    ok = 'yes' if (u == str(north).upper() and d == str(south).upper()) else 'no'
    return {'v': ok, 'verdict': 'the common boundary carries %s at its upper end and %s at its lower end'
            % (u or 'nothing', d or 'nothing')}

# end of code_ends

# shared code: code_any_line
def any_cutout_shows_line(node):
    """Yes when at least one cut-out confirms a printed line."""
    answers = [str(x).strip().lower() for x in ((node or {}).get('answers') or [])]
    n = sum(1 for x in answers if x.startswith('y'))
    return {'v': 'yes' if n >= 1 else 'no', 'n': n,
            'verdict': '%d of the %d cut-outs confirmed a printed line' % (n, len(answers))}

# end of code_any_line

# shared code: code_bearing
def first_answer_text(node):
    s = str((((node or {}).get('answers') or [''])[0])).upper()
    return ''.join(ch for ch in s if ch.isalnum())


def names(node):
    out = []
    for a in ((node or {}).get('answers') or []):
        for tok in str(a).upper().replace(',', ' ').split():
            t = ''.join(ch for ch in tok if ch.isalnum() or ch == '-')
            if t.count('-') == 1 and all(p for p in t.split('-')):
                out.append(t)
    return out


def boundary_points_agree(west_head, west_lines, east_head, east_lines, up, low, key):
    """Yes when sketch end labels, plot headings and both tables all name the right points."""
    k = dict(key or {})
    west_heading, east_heading, upper_end, lower_end = first_answer_text(west_head), first_answer_text(east_head), first_answer_text(up), first_answer_text(low)
    west_names, east_names = names(west_lines), names(east_lines)
    placed = ('123' in west_heading) and ('124' in east_heading)
    sketch = (upper_end == str(k.get('north', '')).upper() and lower_end == str(k.get('south', '')).upper())
    tables = str(k.get('west', '')) in west_names and str(k.get('east', '')) in east_names
    ok = 'yes' if (placed and sketch and tables) else 'no'
    return {'v': ok, 'sketch': 'yes' if sketch else 'no', 'tables': 'yes' if tables else 'no',
            'placed': 'yes' if placed else 'no',
            'verdict': 'sketch ends read %s over %s; headings read %s and %s; west table lists %s; '
                       'east table lists %s' % (upper_end or 'nothing', lower_end or 'nothing', west_heading or 'nothing',
                                                east_heading or 'nothing', '|'.join(west_names) or 'nothing',
                                                '|'.join(east_names) or 'nothing')}

# end of code_bearing
