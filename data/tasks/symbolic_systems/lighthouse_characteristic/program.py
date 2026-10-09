# code: tally_code
def count_yes_answers(result):
    """Count the flash checks whose last yes or no word is yes."""
    answers = result.get('answers') if isinstance(result, dict) else result
    n = 0
    for a in (answers or []):
        if a is None:
            continue
        tokens, word = [], ''
        for ch in str(a).strip().lower():
            if ch.isalpha():
                word += ch
            elif word:
                tokens.append(word); word = ''
        if word:
            tokens.append(word)
        v = None
        for token in tokens:
            if token in ('yes', 'no'):
                v = token
        if v == 'yes':
            n += 1
    return {'n': n, 'answers': answers}

# end of tally_code

# code: eclipse_code
def long_eclipse_score(flashes, strip, want):
    """Score 1 when the dark span after the last flash is the longest only if it should be."""
    flash_boxes = sorted([[float(v) for v in b] for b in flashes['geometry']], key=lambda b: b[1])
    strip_box = [float(v) for v in strip['geometry'][0]]
    L, R = min(strip_box[1], strip_box[3]), max(strip_box[1], strip_box[3])
    if not flash_boxes or R - L < 50.0:
        return {'frac': 0.0, 'degenerate': True}
    lead_gap = max(0.0, flash_boxes[0][1] - L)
    gaps = [max(0.0, flash_boxes[i + 1][1] - flash_boxes[i][3]) for i in range(len(flash_boxes) - 1)]
    trail_gap = max(0.0, R - flash_boxes[-1][3])
    other_gaps = [lead_gap] + gaps
    last_off_longest = trail_gap > max(other_gaps) if other_gaps else True
    ok = bool(last_off_longest) == bool(want)
    return {'frac': 1.0 if ok else 0.0, 'trail': round(trail_gap, 1),
            'others': [round(g, 1) for g in other_gaps],
            'last_off_longest': bool(last_off_longest), 'degenerate': False}

# end of eclipse_code
