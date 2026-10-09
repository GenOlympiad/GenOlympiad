# shared code: code_67f40c00e5b2
def order_ring_boxes(node, colours):
    """Order the bead boxes around the ring by angle and build the colour question for each."""
    import math
    boxes = [[float(v) for v in b] for b in ((node or {}).get('geometry') or [])]
    if not boxes:
        return {'geometry': [], 'n': 0, 'q': '', 'degenerate': True}
    cy = sum((b[0] + b[2]) / 2.0 for b in boxes) / len(boxes)
    cx = sum((b[1] + b[3]) / 2.0 for b in boxes) / len(boxes)
    boxes.sort(key=lambda b: math.atan2((b[0] + b[2]) / 2.0 - cy, (b[1] + b[3]) / 2.0 - cx))
    names = []
    for c in (colours or []):
        if str(c) not in names:
            names.append(str(c))
    question = ('One small coloured piece sits in the MIDDLE of this picture. What colour is that '
         'middle piece? Use ONLY one of these words: ' + ', '.join(names) + '. If the middle '
         'of the picture holds no coloured piece at all, answer none. Answer with exactly '
         'one word.')
    return {'geometry': [[int(round(v)) for v in b] for b in boxes], 'n': len(boxes), 'q': question,
            'palette': names, 'degenerate': False}


def ring_repeats_word(order, word):
    n, k = len(order or ''), len(word or '')
    if n == 0 or k == 0:
        return {'match': False, 'reason': 'empty', 'best_mismatch': None,
                'divisible': False, 'n': n, 'period': k}
    divisible = (n % k == 0)
    best = None
    for seq in (order, order[::-1]):
        for r in range(n):
            rot = seq[r:] + seq[:r]
            target = (word * (n // k + 1))[:n]
            mismatches = sum(1 for a, b in zip(rot, target) if a != b)
            best = mismatches if best is None else min(best, mismatches)
    return {'match': bool(divisible and best == 0), 'best_mismatch': int(best),
            'divisible': bool(divisible), 'n': n, 'period': k}


def band_fraction(err, core, margin):
    f = 1.0 - max(0.0, float(err) - float(core)) / max(float(margin), 1e-9)
    return round(min(1.0, max(0.0, f)), 4)


def ring_law(colour_answers, colours, word, n_expected, per_colour):
    """Read the bead colours in ring order and score the period, closure and colour counts against the pinned word."""
    names = []
    for c in (colours or []):
        if str(c) not in names:
            names.append(str(c))
    order = ''
    counts = {}
    for a in ((colour_answers or {}).get('answers') or []):
        s = str(a or '').strip().lower()
        hit = None
        for nm in names:
            if nm in s:
                hit = nm
                break
        if hit is None:
            continue
        letter = hit[0].upper()
        order += letter
        counts[letter] = counts.get(letter, 0) + 1
    n = len(order)
    if n == 0:
        return {'unreadable': True, 'order': '', 'n': 0, 'counts': {}, 'card_err': None,
                'phase_frac': 0.0, 'closes': 0.0, 'colour_frac': 0.0, 'period_match': False,
                'best_mismatch': None}
    period = ring_repeats_word(order, str(word))
    mismatches = period['best_mismatch']
    phase = max(0.0, 1.0 - 2.0 * float(mismatches) / max(1, n))
    closes = 1.0 if (n == int(n_expected) and period['match']) else 0.0
    letters = sorted(per_colour or {})
    if letters:
        colour_frac = sum(band_fraction(abs(int(counts.get(letter, 0)) - int(per_colour[letter])), 0, 2)
                 for letter in letters) / float(len(letters))
    else:
        colour_frac = 0.0
    return {'unreadable': False, 'order': order, 'n': n, 'counts': counts,
            'card_err': abs(n - int(n_expected)), 'phase_frac': round(phase, 4),
            'closes': closes, 'colour_frac': round(colour_frac, 4),
            'period_match': bool(period['match']), 'best_mismatch': mismatches,
            'divisible': bool(period['divisible'])}

# end of code_67f40c00e5b2

# code: hit_code
def ring_spells_decoy(order, decoy):
    """1.0 if the ring read in either direction from some start spells the decoy word."""
    order_text = str(order or '')
    decoy_text = str(decoy or '')
    if not order_text or len(order_text) != len(decoy_text):
        return 0.0
    best = min(sum(1 for a, b in zip(s[r:] + s[:r], decoy_text) if a != b)
               for s in (order_text, order_text[::-1]) for r in range(len(order_text)))
    return 1.0 if best == 0 else 0.0

# end of hit_code
