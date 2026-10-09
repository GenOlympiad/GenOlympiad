# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, map_answer_to_token
# end of helpers

# shared code: code_zone_radii
def zone_radii_shape(confirm_read, text_read):
    """Lens if the three confirmed zone radii are near the reference and the middle is largest."""
    import re
    confirmed = [str(y).strip().lower().startswith('y') for y in ((confirm_read or {}).get('answers') or [])]
    want = {'2': 8.45, '6': 11.34, '8': 10.69}
    radii = {}
    for i, t in enumerate(((text_read or {}).get('answers') or [])):
        n = re.findall(r'\d+(?:\.\d+)?', str(t))
        if len(n) > 1 and n[0] in want and (i >= len(confirmed) or confirmed[i]):
            radii[n[0]] = float(n[1])
    n_near = sum(1 for k in radii if abs(radii[k] - want[k]) <= 0.12 * want[k])
    return {'val': 'lens' if n_near == 3 and radii.get('6', 0) == max(list(radii.values()) + [0])
            else 'flat', 'verdict': '%d of the three radii sat within an eighth' % n_near}

# end of code_zone_radii

# shared code: code_one_figure
def most_common_figure(confirm_read, text_read):
    """The figure read most often among the confirmed cut outs, or minus 999 if none."""
    import re
    confirmed = [str(y).strip().lower().startswith('y') for y in ((confirm_read or {}).get('answers') or [])]
    figures = []
    for i, t in enumerate(((text_read or {}).get('answers') or [])):
        m = re.search(r'-?\d+(?:\.\d+)?', str(t))
        if m and (i >= len(confirmed) or confirmed[i]):
            figures.append(float(m.group(0)))
    if not figures:
        return {'val': -999.0, 'verdict': 'no cut-out gave a figure'}
    figure = max(set(figures), key=figures.count)
    return {'val': figure, 'verdict': 'figure read as %g from %d cut-out(s)' % (figure, len(figures))}

# end of code_one_figure
