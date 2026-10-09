# code: helpers
from genolympiad.task_helpers import frac_of
# end of helpers

# code: bottom_to_top_code

def buttons_bottom_to_top(button_boxes, button_confirms, button_labels):
    """The labels of the confirmed buttons from the bottom upwards, noting buttons side by side."""
    import re

    def cy(b):
        return (float(b[0]) + float(b[2])) / 2.0

    def cx(b):
        return (float(b[1]) + float(b[3])) / 2.0

    def height(b):
        return abs(float(b[2]) - float(b[0]))

    def yes(a):
        return str(a).strip().lower().startswith('y')

    geo = (button_boxes or {}).get('geometry') or []
    confirms = (button_confirms or {}).get('answers') or []
    labels_read = (button_labels or {}).get('answers') or []
    buttons = []
    for i in range(min(len(geo), len(confirms))):
        if not yes(confirms[i]):
            continue
        m = re.search(r'-?\d+', str(labels_read[i] if i < len(labels_read) else ''))
        buttons.append({'box': geo[i], 'label': m.group() if m else 'none'})
    buttons.sort(key=lambda d: (-cy(d['box']), cx(d['box'])))
    side_by_side = 0
    for i in range(1, len(buttons)):
        a, b = buttons[i - 1]['box'], buttons[i]['box']
        if abs(cy(a) - cy(b)) < 0.5 * max(height(a), height(b)):
            side_by_side += 1
    labels = [d['label'] for d in buttons]
    return {'labels': labels, 'n': len(labels), 'asked': len(confirms),
            'side_by_side_pairs': side_by_side,
            'verdict': '%d of %d framed candidates were confirmed to hold exactly one whole '
                       'button; from the bottom button upwards their printed labels read %s%s'
                       % (len(labels), len(confirms), ', '.join(labels) if labels else '(nothing)',
                          '' if not side_by_side else
                          ' (note: some buttons sit side by side at the same height, which the '
                          'asked-for bottom-to-top arrangement does not allow)')}

# end of bottom_to_top_code

# code: floor_seq_code
def floor_labels_score(seq, gt):
    """The share of floor labels in the reference order, capped at 0.2 if a skipped number appears."""
    import re
    target = [int(x) for x in gt['labels']]
    got = []
    if isinstance(seq,(list,tuple)):
        for x in seq:
            m = re.search(r'-?\d+', str(x))
            if m: got.append(int(m.group(0)))
    else:
        for m in re.findall(r'\d+', str(seq)): got.append(int(m))
    if not got: return {'frac': 0.0, 'no_read': True}
    n = len(target)
    ok = sum(1 for i in range(n) if i < len(got) and got[i] == target[i])
    frac = ok / n
    skipped_numbers = set(int(t) for t in gt['taboo'])
    if skipped_numbers & set(got): frac = min(frac, 0.2)
    return {'frac': round(frac, 4)}

# end of floor_seq_code

# code: qtaboo_code
def skipped_number_question(gt):
    """The question asking whether any skipped floor number is printed."""
    numbers = ' or the number '.join(str(t) for t in gt['taboo'])
    return ("This is a close-up of an elevator button panel. Look at every button "
            "label. Is there a button printed with the number " + numbers + " on this "
            "panel? Answer only 'yes' or 'no'.")

# end of qtaboo_code

# code: taboo_absent_code
def skipped_number_absent(read, gt):
    """1.0 if the judge VLM saw no skipped floor number on the panel."""
    s = str(read).strip().lower()
    if not s or 'unreadable' in s: return {'frac': 0.0, 'unreadable': True}
    present = s.startswith('y') or ('yes' in s[:8])
    return {'frac': 0.0 if present else 1.0}

# end of taboo_absent_code
