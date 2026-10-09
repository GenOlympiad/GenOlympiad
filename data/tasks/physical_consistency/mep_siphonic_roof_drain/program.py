# shared code: code_grow
def collector_grows_to_gable(node, size_boxes):
    """Check the collector size tags never shrink from the far end to the gable and grow overall."""
    def geo(n):
        g = n.get('geometry') if isinstance(n, dict) else None
        return [b for b in (g or []) if isinstance(b, (list, tuple)) and len(b) >= 4]
    answers = node.get('answers') if isinstance(node, dict) else None
    answers = list(answers) if isinstance(answers, (list, tuple)) else []
    boxes = geo(size_boxes)
    rows = []
    for i, x in enumerate(answers):
        d = ''.join(c for c in str(x) if c.isdigit() or c == '.').strip('.').split('.')[0]
        if d and i < len(boxes):
            cx = (float(boxes[i][1]) + float(boxes[i][3])) / 2.0
            rows.append((cx, int(d)))
    rows.sort()
    sizes = [v for _, v in rows]
    up = all(sizes[i] <= sizes[i + 1] for i in range(len(sizes) - 1))
    ok = 'yes' if len(sizes) >= 3 and up and sizes[-1] > sizes[0] else 'no'
    return {'ok': ok, 'verdict': 'the collector is sized %s reading from the far end (page left) to the gable (page right), each size tag placed by its own ring x centre' % (sizes,)}

# end of code_grow

# code: flat_code
def collector_uniform(node):
    """Check the collector carries at least three size tags that are all the same."""
    vals = []
    for x in ((node or {}).get('answers') or []):
        d = ''.join(c for c in str(x) if c.isdigit() or c == '.').strip('.')
        if d:
            vals.append(d)
    ok = 'yes' if len(vals) >= 3 and len(set(vals)) == 1 else 'no'
    return {'ok': ok, 'verdict': 'the collector is tagged %s along its length' % (vals,)}

# end of flat_code

# code: bal_code
def branches_balanced(node):
    """Check the three branch pipes carry the same size tag."""
    vals = []
    for x in ((node or {}).get('answers') or []):
        d = ''.join(c for c in str(x) if c.isdigit() or c == '.').strip('.')
        if d:
            vals.append(d)
    ok = 'yes' if len(vals) == 3 and len(set(vals)) == 1 else 'no'
    return {'ok': ok, 'verdict': 'the three branches are tagged %s' % (vals,)}

# end of bal_code
