# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_enumerated_items
# end of helpers

# shared code: code_2a7924a29f02
def count_ratio_gap(a, b, k, off):
    """How far the second count is from k times the first count plus the offset."""
    if a is None or b is None:
        return 999
    return abs(b - (k * a + off))

def implausible(a, b, lo):
    """Flag 1 when either count is missing or below the minimum."""
    return 1 if (a is None or b is None or a < lo or b < lo) else 0

# end of code_2a7924a29f02

# code: floor_score_code
def floor_score(count, minimum):
    """Score 1 at or above the minimum count, losing a third per missing piece."""
    if count is None:
        return 0.0
    if count >= minimum:
        return 1.0
    return max(0.0, 1.0 - (minimum - count) / 3.0)

# end of floor_score_code

# code: strips_k2_code
def strips_k2(anchor, k):
    """Split the boxed wall into k equal vertical strips, left to right."""
    anchor_boxes = (anchor or {}).get('geometry') or []
    if not anchor_boxes: return []
    y0, x0, y1, x1 = [float(v) for v in anchor_boxes[0][:4]]
    y0, y1 = min(y0, y1), max(y0, y1)
    x0, x1 = min(x0, x1), max(x0, x1)
    return [[y0, x0 + (x1 - x0) * i / float(k), y1, x0 + (x1 - x0) * (i + 1) / float(k)]
            for i in range(int(k))]

# end of strips_k2_code

# code: strip_total_k2_code
def strip_total_k2(node, what):
    """Add up the numbers read strip by strip, refusing if any strip gave no number."""
    import re
    answers = (node or {}).get('answers') or []
    if not answers: return {'n': -1, 'unread': True, 'refused': True, 'verdict': 'no strip was read'}
    strip_counts = []
    for a in answers:
        m = re.findall(r'\d+', str(a if a is not None else ''))
        if not m: return {'n': -1, 'unread': True, 'refused': True, 'verdict': 'a strip returned no number -> nothing was counted'}
        strip_counts.append(int(m[0]))
    return {'n': sum(strip_counts), 'per_strip': strip_counts, 'unread': False,
            'verdict': '%s counted strip by strip: %s = %d' % (what, ' + '.join(str(v) for v in strip_counts), sum(strip_counts))}

# end of strip_total_k2_code

# code: strips_k3_code
def strips_k3(anchor, k):
    """Split the boxed wall into k equal vertical strips, left to right."""
    anchor_boxes = (anchor or {}).get('geometry') or []
    if not anchor_boxes: return []
    y0, x0, y1, x1 = [float(v) for v in anchor_boxes[0][:4]]
    y0, y1 = min(y0, y1), max(y0, y1)
    x0, x1 = min(x0, x1), max(x0, x1)
    return [[y0, x0 + (x1 - x0) * i / float(k), y1, x0 + (x1 - x0) * (i + 1) / float(k)]
            for i in range(int(k))]

# end of strips_k3_code

# code: strip_total_k3_code
def strip_total_k3(node, what):
    """Add up the numbers read strip by strip, refusing if any strip gave no number."""
    import re
    answers = (node or {}).get('answers') or []
    if not answers: return {'n': -1, 'unread': True, 'refused': True, 'verdict': 'no strip was read'}
    strip_counts = []
    for a in answers:
        m = re.findall(r'\d+', str(a if a is not None else ''))
        if not m: return {'n': -1, 'unread': True, 'refused': True, 'verdict': 'a strip returned no number -> nothing was counted'}
        strip_counts.append(int(m[0]))
    return {'n': sum(strip_counts), 'per_strip': strip_counts, 'unread': False,
            'verdict': '%s counted strip by strip: %s = %d' % (what, ' + '.join(str(v) for v in strip_counts), sum(strip_counts))}

# end of strip_total_k3_code

# code: strips_k4_code
def strips_k4(anchor, k):
    """Split the boxed wall into k equal vertical strips, left to right."""
    anchor_boxes = (anchor or {}).get('geometry') or []
    if not anchor_boxes: return []
    y0, x0, y1, x1 = [float(v) for v in anchor_boxes[0][:4]]
    y0, y1 = min(y0, y1), max(y0, y1)
    x0, x1 = min(x0, x1), max(x0, x1)
    return [[y0, x0 + (x1 - x0) * i / float(k), y1, x0 + (x1 - x0) * (i + 1) / float(k)]
            for i in range(int(k))]

# end of strips_k4_code

# code: strip_total_k4_code
def strip_total_k4(node, what):
    """Add up the numbers read strip by strip, refusing if any strip gave no number."""
    import re
    answers = (node or {}).get('answers') or []
    if not answers: return {'n': -1, 'unread': True, 'refused': True, 'verdict': 'no strip was read'}
    strip_counts = []
    for a in answers:
        m = re.findall(r'\d+', str(a if a is not None else ''))
        if not m: return {'n': -1, 'unread': True, 'refused': True, 'verdict': 'a strip returned no number -> nothing was counted'}
        strip_counts.append(int(m[0]))
    return {'n': sum(strip_counts), 'per_strip': strip_counts, 'unread': False,
            'verdict': '%s counted strip by strip: %s = %d' % (what, ' + '.join(str(v) for v in strip_counts), sum(strip_counts))}

# end of strip_total_k4_code
