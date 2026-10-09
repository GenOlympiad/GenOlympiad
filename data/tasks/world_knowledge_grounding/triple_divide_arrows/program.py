# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_water_set
def named_waters(node):
    """The sorted list of the three receiving waters named on the marker."""
    sk = (('pacific', 'pacific'), ('mexico', 'mexico'), ('hudson', 'hudson'))
    got = []
    for raw in (node or {}).get('answers') or []:
        hit = [v for k, v in sk if k in str(raw).lower()]
        got.append(hit[0] if hit else 'other')
    seq = '|'.join(sorted(got))
    return {'seq': seq, 'n': len(got), 'verdict': 'waters named, sorted: %s' % (seq or 'nothing')}

# end of code_water_set

# shared code: code_divide_pairs
def pair_rivers_to_seas(rivers, sea):
    """Check each river block names a river draining to the sea named in the same block."""
    rk = (('columbia', 'p'), ('flathead', 'p'), ('missouri', 'g'), ('mississippi', 'g'), ('marias', 'g'), ('saskatchewan', 'h'), ('nelson', 'h'), ('mary', 'h'))
    sk = (('pacific', 'p'), ('mexico', 'g'), ('hudson', 'h'))
    sea_answers = (sea or {}).get('answers') or []
    got = []
    for i, raw in enumerate((rivers or {}).get('answers') or []):
        one = ([v for k, v in rk if k in str(raw).lower()] or ['?'])[0]
        two = ([v for k, v in sk if k in str(sea_answers[i] if i < len(sea_answers) else '').lower()] or ['?'])[0]
        got.append(one + two)
    good = sorted(got) == ['gg', 'hh', 'pp']
    return {'state': 'paired' if good else 'crossed', 'n': len(got), 'verdict': 'blocks read %s against the wanted gg hh pp' % (' '.join(got) or 'nothing')}

# end of code_divide_pairs

# shared code: code_arrow_spread
def arrows_apart(node):
    """Check the three arrows read as three different directions."""
    got = []
    for raw in (node or {}).get('answers') or []:
        got.append(''.join(c for c in str(raw).lower() if c.isalpha()))
    good = len(got) == 3 and len(set(got)) == 3
    return {'state': 'apart' if good else 'doubled', 'n': len(got),
            'verdict': 'arrow directions read %s' % (' '.join(got) or 'nothing')}

# end of code_arrow_spread
