# code: rail_code
def rail_part_labels(node):
    """The sorted part labels read at the junctions on the return rail, or a refusal if none."""
    labels = []
    for raw in (node or {}).get('answers') or []:
        t = ''.join(c for c in str(raw or '').lower() if c.isalnum())
        if t and t not in labels:
            labels.append(t)
    if not labels:
        return {'seq': 'none', 'refused': True,
                'verdict': 'no junction cut-out came back with a part label -> abstain'}
    labels.sort()
    return {'seq': ','.join(labels), 'verdict': 'the rail collects %s' % ','.join(labels)}

# end of rail_code

# code: barend_code
def diode_bar_end(node):
    """The end of the diode where most reads place its bar, or a refusal if none came back."""
    answers = [str(a or '').strip().lower() for a in (node or {}).get('answers') or []]
    answers = [a.split()[0] for a in answers if a]
    if not answers:
        return {'end': 'none', 'refused': True,
                'verdict': 'the cut-out of the diode came back empty -> abstain'}
    majority_end = max(set(answers), key=answers.count)
    return {'end': majority_end, 'verdict': 'the bar of the diode stands at the %s' % majority_end}

# end of barend_code
