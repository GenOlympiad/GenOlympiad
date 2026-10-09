# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: pair_box_code
def union_glass_boxes(glasses):
    """Join the confirmed glass boxes into one window, refusing if fewer than two."""
    g = (glasses or {}).get('geometry') or []
    boxes = [[float(v) for v in r[:4]] for r in g if r and len(r) >= 4]
    if len(boxes) < 2:
        return {'geometry': [], 'degenerate': True, 'refused': True,
                'verdict': 'fewer than two glasses were confirmed, so there is no pair to compare'}
    y0 = min(r[0] for r in boxes); x0 = min(r[1] for r in boxes)
    y1 = max(r[2] for r in boxes); x1 = max(r[3] for r in boxes)
    return {'geometry': [[y0, x0, y1, x1]], 'degenerate': False, 'n_glasses': len(boxes),
            'verdict': 'the %d confirmed glass boxes were unioned into one window' % len(boxes)}

# end of pair_box_code

# code: joint_code
import re


def pick(a):
    if not isinstance(a, str):
        return None
    s = a.strip().lower()
    m = re.match(r'^[\(\[]?([ab])[\)\].:,\s]', s + ' ')
    if m:
        return m.group(1)
    m = re.search(r'\boption\s*([ab])\b', s)
    if m:
        return m.group(1)
    m = re.search(r'\b([ab])\b', s)
    if m:
        return m.group(1)
    return None


def level_and_ice_score(sg, ice):
    """Score 1 when the level read is 'a' and only the left glass still holds ice."""
    level_choice = pick(sg)
    answers = [str(x).strip().lower() for x in ((ice or {}).get('answers') or [])]
    if level_choice is None or len(answers) < 2:
        return 0.0
    left_ice = answers[0].startswith('y')
    right_ice = answers[1].startswith('y')
    return 1.0 if (level_choice == 'a' and left_ice and not right_ice) else 0.0

# end of joint_code
