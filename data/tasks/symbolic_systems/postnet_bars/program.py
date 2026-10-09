# code: helpers
from genolympiad.task_helpers import map_items_to_tokens
# end of helpers

# shared code: code_f1f2910e6d2c
def digit_group_boxes(bar_boxes, bars_per_digit):
    """Sort the bar boxes left to right, drop the two frame bars and box each group of bars that codes one digit."""
    geometry = bar_boxes.get('geometry') if isinstance(bar_boxes, dict) else bar_boxes
    if not geometry:
        return {'boxes': None, 'n': 0, 'no_read': True}
    bars = []
    for b in geometry:
        ymin, xmin, ymax, xmax = [float(v) for v in b[:4]]
        bars.append((0.5 * (xmin + xmax), ymin, xmin, ymax, xmax))
    bars.sort(key=lambda r: r[0])
    n = len(bars)
    bars_per_digit = int(bars_per_digit)
    inner = n - 2
    if n < bars_per_digit + 2 or inner % bars_per_digit != 0:
        return {'boxes': None, 'n': float(n), 'no_read': True}
    ytop = min(r[1] for r in bars)
    ybot = max(r[3] for r in bars)
    out = []
    for i in range(inner // bars_per_digit):
        group = bars[1 + i * bars_per_digit: 1 + (i + 1) * bars_per_digit]
        pitch = (group[-1][0] - group[0][0]) / float(bars_per_digit - 1) if bars_per_digit > 1 else 20.0
        out.append([ytop, group[0][2] - 0.28 * pitch, ybot, group[-1][4] + 0.28 * pitch])
    return {'boxes': out, 'n': float(n), 'no_read': False}

# end of code_f1f2910e6d2c

# code: postnet_frac_code
def digits_read_correctly(group_answers, gt):
    """The share of digit groups whose full and half bars match the reference, capped at 0.25 unless all match."""
    target_groups = gt['digit_groups']
    answers = group_answers.get('answers') if isinstance(group_answers, dict) else group_answers
    if not answers or len(answers) != len(target_groups):
        return {'frac': 0.0, 'no_read': True}
    got = []
    for ans in answers:
        toks = []
        for w in str(ans).lower().replace(',', ' ').replace('-', ' ').split():
            w = w.strip('.:;()')
            if w in ('full', 'tall'):
                toks.append(1)
            elif w in ('half', 'short'):
                toks.append(0)
        got.append(toks)
    want = len(target_groups[0])
    for toks in got:
        if len(toks) != want:
            return {'frac': 0.0, 'no_read': True, 'read': got}
    n_digits = len(target_groups)
    ok = 0
    for i in range(n_digits):
        if got[i] == list(target_groups[i]):
            ok += 1
    frac = round(ok / float(n_digits), 4)
    if ok < n_digits:
        frac = min(frac, 0.25)
    return {'frac': frac, 'no_read': False, 'read': got}

# end of postnet_frac_code

# code: nb_code
def bar_count_matches(groups, want):
    """1.0 if the number of bars equals the wanted number."""
    if not isinstance(groups, dict) or groups.get('n') is None:
        return {'frac': 0.0, 'no_read': True}
    n = int(groups['n'])
    if n <= 0:
        return {'frac': 0.0, 'no_read': True}
    return {'frac': 1.0 if n == int(want) else 0.0, 'n': n, 'no_read': False}

# end of nb_code
