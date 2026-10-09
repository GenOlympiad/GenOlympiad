# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_1100347d96cb
def _states(sb, top, mid, bot):
    n = int((sb or {}).get('n_stacks') or 0)
    cols = []
    for node in (top, mid, bot):
        a = list((node or {}).get('answers') or [])
        if n <= 0 or len(a) != n:
            return None
        cols.append(a)
    got = []
    for i in range(n):
        lit = []
        for j in range(3):
            a = str(cols[j][i] or '').strip().lower()
            on = a.startswith('lit') or a.startswith('on') or 'glow' in a
            off = a.startswith('dark') or a.startswith('off') or 'unlit' in a or 'not lit' in a
            if not on and not off:
                return None
            if on and not off:
                lit.append(j)
        got.append('RYG'[lit[0]] if len(lit) == 1 else '-')
    return got


def all_stacks_match(stack_boxes, top, mid, bot, target):
    """Score 1 when every stack's read lamp state equals the reference state in order."""
    got = _states(stack_boxes, top, mid, bot)
    if got is None:
        return {'frac': 0.0, 'unreadable': True, 'read': None}
    targets = [str(x).strip().upper() for x in (target or [])]
    all_match = (len(got) == len(targets) and all(a == b for a, b in zip(got, targets)))
    return {'frac': 1.0 if all_match else 0.0, 'unreadable': False,
            'read': '|'.join(got), 'want': '|'.join(targets)}


def share_stacks_match(stack_boxes, top, mid, bot, target):
    """The share of stacks whose read lamp state equals the reference state."""
    got = _states(stack_boxes, top, mid, bot)
    if got is None:
        return {'frac': 0.0, 'unreadable': True, 'read': None}
    targets = [str(x).strip().upper() for x in (target or [])]
    if not targets:
        return {'frac': 0.0, 'unreadable': False, 'read': '|'.join(got)}
    matched = sum(1 for i, b in enumerate(targets) if i < len(got) and got[i] == b)
    return {'frac': round(matched * 1.0 / len(targets), 4), 'unreadable': False,
            'read': '|'.join(got), 'want': '|'.join(targets), 'matched': matched}

# end of code_1100347d96cb

# shared code: code_43e0fd0fd6c4
def order_stacks(stack_reads):
    """Order the found light-stack boxes left to right, refusing if there are none."""
    boxes = [[float(v) for v in b] for b in ((stack_reads or {}).get('geometry') or [])]
    if not boxes:
        return {'geometry': None, 'n_stacks': 0, 'unreadable': True}
    boxes.sort(key=lambda b: (b[1] + b[3]) / 2.0)
    return {'geometry': boxes, 'n_stacks': len(boxes), 'unreadable': False}

# end of code_43e0fd0fd6c4
