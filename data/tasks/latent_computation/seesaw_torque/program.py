# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_listed_items
# end of helpers

# shared code: code_f6cb64d642b3
def stack_count_read(node):
    """The last number in the read of the confirmed block stack."""
    answers = (node or {}).get('answers') or []
    raw = str(answers[0] if answers else '')
    digit_runs = ''.join(c if c.isdigit() else ' ' for c in raw).split()
    n = int(digit_runs[-1]) if digit_runs else None
    return {'n': n, 'unread': n is None, 'read': raw.strip() or None,
            'verdict': 'confirmed stack holds %s blocks' % (n if n is not None else '?')}

# end of code_f6cb64d642b3

# code: arms_code

def arm_length_ratio(pivot, left_group, right_group, right_confirms):
    """The right arm over the left arm, measured from the pivot to each block group."""
    def cx(node):
        b = (node or {}).get('geometry') or []
        if not b:
            return None
        box = [float(v) for v in b[0]]
        return (box[1] + box[3]) / 2.0

    def group_cx(node, cr):
        g = (node or {}).get('geometry') or []
        ans = (cr.get('answers') if isinstance(cr, dict) else cr) or []
        xs = []
        for i in range(min(len(g), len(ans))):
            if not str(ans[i]).strip().lower().startswith('y'):
                continue
            box = [float(v) for v in g[i][:4]]
            xs.append(min(box[1], box[3]))
            xs.append(max(box[1], box[3]))
        if not xs:
            return None
        return (min(xs) + max(xs)) / 2.0

    pivot_x, left_x, right_x = cx(pivot), cx(left_group), group_cx(right_group, right_confirms)
    if pivot_x is None or left_x is None or right_x is None:
        return {'dist_ratio': None, 'degenerate': True, 'refused': True,
                'verdict': 'a block group or the pivot was never confirmed'}
    left_arm, right_arm = abs(left_x - pivot_x), abs(right_x - pivot_x)
    if left_arm < 15.0 or right_arm < 15.0:
        return {'dist_ratio': None, 'd_left': round(left_arm, 1), 'd_right': round(right_arm, 1),
                'degenerate': True,
                'verdict': 'a block group sits on the pivot (arm %.0f/%.0f per-mille)'
                           % (left_arm, right_arm)}
    ratio = right_arm / left_arm
    return {'dist_ratio': round(ratio, 4), 'd_left': round(left_arm, 1), 'd_right': round(right_arm, 1),
            'pivot_x': round(pivot_x, 1), 'degenerate': False,
            'verdict': 'arms %.0f : %.0f per-mille -> d_right/d_left = %.3f' % (right_arm, left_arm, ratio)}

# end of arms_code

# code: tilt_code
def tilt_direction_score(tilt_read, reference):
    """Score 1 when the read plank tilt, left down, level or right down, matches the reference."""
    answers = (tilt_read or {}).get('answers') or []
    answer = str(answers[0] if answers else '').strip().lower()
    sign = None
    if any(k in answer for k in ('same', 'level', 'equal', 'horizontal')):
        sign = 0
    elif 'lower' in answer or 'left end is down' in answer:
        sign = -1
    elif 'higher' in answer or 'right end is down' in answer:
        sign = 1
    elif 'left' in answer:
        sign = -1
    elif 'right' in answer:
        sign = 1
    want = int(reference.get('tilt_sign', 0))
    frac = 1.0 if (sign is not None and sign == want) else 0.0
    names = {-1: 'left end lower', 0: 'both ends level', 1: 'right end lower'}
    return {'frac': frac, 'sign': sign, 'want': want,
            'verdict': 'plank reads "%s" = %s (sign %s), spec %s -> frac %.1f'
                       % (answer or 'unparsed', names.get(sign, 'unparsed'), sign,
                          names.get(want, want), frac)}

# end of tilt_code

# code: n_yes_code

def count_yes_reads(reads):
    """Count the cut-out reads that say yes, refusing if nothing usable came back."""
    answers = (reads.get('answers') if isinstance(reads, dict) else reads) or []
    if not answers: return {'n': 0.0, 'unread': True, 'refused': True}
    ok = [s for s in [str(x).strip().lower() for x in answers] if s and not s.startswith('none')]
    return {'n': float(sum(1 for s in ok if s.startswith('y'))), 'unread': not ok, 'refused': not ok}

# end of n_yes_code
