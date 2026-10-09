# shared code: code_turn_set
def speaker_turns(number_reads, vera_reads, otto_reads):
    """List where Vera or Otto faces a different side than in the first frame read."""
    def side(raw):
        s = str(raw).strip().lower()
        if 'left' in s:
            return 'left'
        if 'right' in s:
            return 'right'
        return None
    frame_numbers = []
    for a in (number_reads or {}).get('answers') or []:
        digits = ''.join(c for c in str(a) if c.isdigit())
        frame_numbers.append(digits if digits else None)
    vera_sides = [side(x) for x in ((vera_reads or {}).get('answers') or [])]
    otto_sides = [side(x) for x in ((otto_reads or {}).get('answers') or [])]
    rows = {}
    for i, n in enumerate(frame_numbers):
        if not n or i >= len(vera_sides) or i >= len(otto_sides):
            continue
        if vera_sides[i] is None or otto_sides[i] is None:
            continue
        rows.setdefault(n, (vera_sides[i], otto_sides[i]))
    if len(rows) < 2:
        return {'turns': 'fewer than two frames could be read',
                'read': len(rows),
                'verdict': 'only %d frame(s) gave a number and both facings' % len(rows)}
    order = sorted(rows, key=lambda s: (len(s), s))
    base_v, base_o = rows[order[0]]
    turns = []
    for n in order[1:]:
        v, o = rows[n]
        if v != base_v:
            turns.append('vera turns at %s' % n)
        if o != base_o:
            turns.append('otto turns at %s' % n)
    if not turns:
        return {'turns': 'nobody changes hands anywhere on the page', 'read': len(rows),
                'verdict': 'across the %d frames read, neither speaker ever changes hands' % len(rows)}
    turn_text = ', '.join(sorted(set(turns)))
    return {'turns': turn_text, 'read': len(rows),
            'verdict': 'across the %d frames read: %s' % (len(rows), turn_text)}

# end of code_turn_set

# shared code: code_side_vote
def majority_side(node):
    """The side, left or right, named most often across the answers."""
    counts = {}
    for raw in (node or {}).get('answers') or []:
        s = str(raw).strip().lower()
        side = 'left' if 'left' in s else ('right' if 'right' in s else None)
        if side:
            counts[side] = counts.get(side, 0) + 1
    if not counts:
        return {'txt': 'neither side was read',
                'verdict': 'the cut-out named neither side'}
    best = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    return {'txt': best, 'verdict': 'the first set-up puts her facing %s' % best}

# end of code_side_vote
