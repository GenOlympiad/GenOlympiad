# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_item_side
def item_side(confirms, texts):
    """List the confirmed items as view and side, such as dorsal little or palm thumb."""
    confirmed = [str(y).strip().lower().startswith('y') for y in ((confirms or {}).get('answers') or [])]
    rows = []
    for i, t in enumerate(((texts or {}).get('answers') or [])):
        s = str(t).strip().lower()
        view = 'dorsal' if 'dors' in s else ('palm' if 'palm' in s else
             ('fragment' if 'frag' in s else ''))
        side = 'little' if 'little' in s else ('thumb' if 'thumb' in s else '')
        if view and side and (i >= len(confirmed) or confirmed[i]):
            rows.append('%s %s' % (view, side))
    seq = ', '.join(sorted(set(rows)))
    return {'seq': seq, 'n': len(rows), 'verdict': 'travel read as: %s' % (seq or 'none')}

# end of code_item_side

# shared code: code_travel_group
def travel_group(confirms, texts):
    """Whether the fragment moves with the dorsal wire and apart from the palm wire."""
    import re
    confirmed = [str(y).strip().lower().startswith('y') for y in ((confirms or {}).get('answers') or [])]
    travels = {}
    for i, t in enumerate(((texts or {}).get('answers') or [])):
        s = str(t).strip().lower()
        view = 'd' if 'dors' in s else ('p' if 'palm' in s else ('f' if 'frag' in s else ''))
        numbers = re.findall(r'\d+(?:\.\d+)?', s)
        if view and numbers and (i >= len(confirmed) or confirmed[i]):
            travels[view] = float(numbers[-1])
    grouped = len(travels) > 2 and abs(travels['d'] - travels['f']) <= 3 and abs(travels['f'] - travels['p']) > 3
    return {'val': 'the fragment travels with the dorsal wire' if grouped else 'no grouping', 'verdict': 'travels read as %s' % sorted(travels.items())}

# end of code_travel_group
