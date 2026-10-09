# code: linkage_code
def check_flip_and_shrink(letter_boxes, handedness_reads):
    """1 if the first reflection flips handedness and the images shrink outward, else 0."""
    boxes = (letter_boxes or {}).get('geometry') or []
    answers = [str(a or '').strip().lower() for a in ((handedness_reads or {}).get('answers') or [])]
    out = {'frac': 0.0, 'n_letters': len(boxes), 'why': ''}
    if len(boxes) < 3 or len(answers) != len(boxes):
        out['why'] = ('need the original letter plus at least two reflections; '
                      'got %d letters and %d handedness answers' % (len(boxes), len(answers)))
        return out
    items = sorted(zip(boxes, answers), key=lambda t: (float(t[0][1]) + float(t[0][3])) / 2.0)
    heights = [float(b[2]) - float(b[0]) for b, _ in items]
    k = max(range(len(heights)), key=lambda i: heights[i])

    def decays(idxs):
        hh = [heights[i] for i in idxs]
        return len(hh) >= 2 and all(b < a * 0.97 for a, b in zip(hh, hh[1:]))

    right = list(range(k + 1, len(heights)))
    left = list(range(k - 1, -1, -1))
    reflection_arm = right if decays(right) else (left if decays(left) else None)
    out['heights_left_to_right'] = [round(h, 1) for h in heights]
    if reflection_arm is None:
        out['why'] = ('no reflection arm shrinks monotonically outward -- letter heights '
                      'left to right are %s' % out['heights_left_to_right'])
        return out

    def parity(s):
        l, r = s.find('left'), s.find('right')
        if r >= 0 and (l < 0 or r < l):
            return 'stem-body-right'
        if l >= 0:
            return 'stem-body-left'
        return None

    original_side, first_side = parity(items[k][1]), parity(items[reflection_arm[0]][1])
    if original_side is None or first_side is None:
        out['why'] = ('which side the letter body sits on is not readable (original answered '
                      '%r, first reflection %r)' % (items[k][1], items[reflection_arm[0]][1]))
        return out
    out['original'] = original_side
    out['first_reflection'] = first_side
    out['decay_chain'] = [round(heights[k], 1)] + [round(heights[i], 1) for i in reflection_arm]
    if original_side == first_side:
        out['why'] = ('the first reflection has the SAME handedness as the original (letter body '
                      'on the same side, %s) -- no parity flip; decay chain %s'
                      % (original_side, out['decay_chain']))
        return out
    out['frac'] = 1.0
    out['why'] = ('parity flips (original %s -> first reflection %s) AND the images decay '
                  'outward %s -> frac 1.0' % (original_side, first_side, out['decay_chain']))
    return out

# end of linkage_code
