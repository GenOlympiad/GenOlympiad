# shared code: code_4a840a3f278f
def edge_and_label_numbers(edge_read, label_read):
    """The last number in the edge read and in the label read, flagged if either is missing."""
    import re
    def last_number(node, i=0):
        ans = (node or {}).get('answers') or []
        if i >= len(ans) or ans[i] is None:
            return None
        s = str(ans[i]).replace(',', '.')
        if 'none' in s.lower():
            return None
        m = re.findall(r'-?\d+(?:\.\d+)?', s)
        return float(m[-1]) if m else None
    edge, label = last_number(edge_read), last_number(label_read)
    return {'edge': edge, 'label': label, 'bad': (edge is None or label is None)}

# end of code_4a840a3f278f

# shared code: code_c96f751a1ae5
def scale_is_numbered(pm):
    """True when the read says the scale carries printed numbers."""
    answers = (pm or {}).get('answers') or []
    a = str(answers[0]).strip().lower() if (answers and answers[0] is not None) else ''
    return {'numbered': a.startswith('y'), 'bad': (not a.startswith('y'))}

# end of code_c96f751a1ae5

# code: eqcode
def edge_label_err(edge, label):
    """The gap between the edge reading and the label reading, or 9.99 if either is missing."""
    if edge is None or label is None:
        return 9.99
    return round(abs(float(edge) - float(label)), 4)

# end of eqcode

# code: scale_window_edge_label_code
def scale_window_edge_label(scale_read):
    """A crop strip across the frame along the boxed scale, padded to show its labels."""
    geometry = (scale_read or {}).get('geometry') or []
    bad = {'bbox': [0.0, 0.0, 1.0, 1.0], 'degenerate': True, 'refused': True}
    if not geometry: return bad
    ymin, xmin, ymax, xmax = [float(v) for v in geometry[0][:4]]
    h, w = abs(ymax - ymin), abs(xmax - xmin)
    if h < 5.0 or w < 5.0: return bad
    if w >= h: x0, x1 = 0.0, 1000.0; y0, y1 = max(0.0, ymin - 1.4 * h), min(1000.0, ymax + 1.4 * h)
    else: y0, y1 = 0.0, 1000.0; x0, x1 = max(0.0, xmin - 1.4 * w), min(1000.0, xmax + 1.4 * w)
    return {'bbox': [round(x0 / 1000.0, 4), round(y0 / 1000.0, 4), round(x1 / 1000.0, 4), round(y1 / 1000.0, 4)], 'degenerate': False}
# end of scale_window_edge_label_code

# code: scale_window_edge_only_code
def scale_window_edge_only(scale_read):
    """A crop strip across the frame along the boxed scale, padded on both sides."""
    geometry = (scale_read or {}).get('geometry') or []
    bad = {'bbox': [0.0, 0.0, 1.0, 1.0], 'degenerate': True, 'refused': True}
    if not geometry: return bad
    ymin, xmin, ymax, xmax = [float(v) for v in geometry[0][:4]]
    h, w = abs(ymax - ymin), abs(xmax - xmin)
    if h < 5.0 or w < 5.0: return bad
    if w >= h: x0, x1 = 0.0, 1000.0; y0, y1 = max(0.0, ymin - 1.4 * h), min(1000.0, ymax + 1.4 * h)
    else: y0, y1 = 0.0, 1000.0; x0, x1 = max(0.0, xmin - 1.4 * w), min(1000.0, xmax + 1.4 * w)
    return {'bbox': [round(x0 / 1000.0, 4), round(y0 / 1000.0, 4), round(x1 / 1000.0, 4), round(y1 / 1000.0, 4)], 'degenerate': False}
# end of scale_window_edge_only_code
