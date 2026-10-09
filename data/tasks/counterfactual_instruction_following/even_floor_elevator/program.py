# code: ringed_button_code

def read_ringed_button(button_boxes, button_confirms, ring_reads, label_reads):
    """The label of the one confirmed button circled in red, if exactly one has it."""
    def yes(a):
        return str(a).strip().lower().startswith('y')

    geometry = (button_boxes or {}).get('geometry') or []
    confirms = (button_confirms or {}).get('answers') or []
    circled = (ring_reads or {}).get('answers') or []
    labels = (label_reads or {}).get('answers') or []
    buttons = []
    for i in range(min(len(geometry), len(confirms))):
        if not yes(confirms[i]):
            continue
        buttons.append({'box': geometry[i],
                        'ringed': yes(circled[i]) if i < len(circled) else False,
                        'label': str(labels[i]).strip() if i < len(labels) and labels[i] else 'none'})
    marked = [b for b in buttons if b['ringed']]
    result = {'n_buttons': len(buttons), 'n_ringed': len(marked),
           'labels': [b['label'] for b in buttons]}
    if len(marked) != 1:
        result['number'] = ('the panel does not carry exactly one button with a red ring drawn '
                         'round it, so no ringed button can be read')
        result['verdict'] = ('%d buttons were confirmed one at a time and %d of them were confirmed '
                          'to have a red ring drawn round them, so there is no single ringed '
                          'button to read' % (len(buttons), len(marked)))
        return result
    result['number'] = marked[0]['label']
    result['verdict'] = ('%d buttons were confirmed one at a time; exactly one of them has a red ring '
                      'drawn round it and the face of that button reads %s'
                      % (len(buttons), marked[0]['label']))
    return result

# end of ringed_button_code

# code: chk_code
def number_matches_reference(answer, want):
    """Score 1 if the first number in the answer equals the expected floor."""
    import re
    if answer is None or isinstance(answer, dict): return 0.0
    t = str(answer).strip().lower().replace(',', '').replace(' ', '')
    m = re.search(r'-?\d+', t)
    if not m: return 0.0
    return 1.0 if int(m.group(0)) == int(want) else 0.0

# end of chk_code
