# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_aperture_hands
def read_opening_sides(node):
    """Read which side each shell opens on; five right and one left counts as normal."""
    sides = []
    for raw in (node or {}).get('answers') or []:
        letters = ''.join(c for c in str(raw).lower() if c.isalpha())
        sides.append('l' if letters[:1] == 'l' else ('r' if letters[:1] == 'r' else '?'))
    seq = ''.join(sides)
    good = seq.count('r') == 5 and seq.count('l') == 1
    return {'state': 'normal' if good else 'wrong', 'n': len(sides),
            'verdict': 'openings read %s' % (seq or 'nothing')}

# end of code_aperture_hands

# shared code: code_mirror_pairs
def openings_mirror_coils(opening_reads, coil_reads):
    """Check the one shell opening on the left is also the one coiled anticlockwise."""
    coils = (coil_reads or {}).get('answers') or []
    openings, coil_turns = [], []
    for i, raw in enumerate((opening_reads or {}).get('answers') or []):
        openings.append('l' if str(raw).strip().lower()[:1] == 'l' else 'r')
        txt = ''.join(c for c in str(coils[i] if i < len(coils) else '').lower() if c.isalpha())
        coil_turns.append('a' if txt[:4] == 'anti' or txt[:7] == 'counter' else 'c')
    left_openings = [i for i, v in enumerate(openings) if v == 'l']
    anticlockwise_coils = [i for i, v in enumerate(coil_turns) if v == 'a']
    good = len(openings) == 6 and left_openings == anticlockwise_coils and len(left_openings) == 1
    return {'state': 'mirrored' if good else 'turned', 'n': len(openings), 'verdict': 'openings %s against coils %s' % (''.join(openings) or 'nothing', ''.join(coil_turns) or 'nothing')}

# end of code_mirror_pairs

# shared code: code_slip_binding
def slip_beside_odd_shell(opening_reads, slip_reads):
    """Check the slip lies beside the one shell whose opening is on the left."""
    slip_answers = (slip_reads or {}).get('answers') or []
    openings = ['l' if str(r).strip().lower()[:1] == 'l' else 'r' for r in ((opening_reads or {}).get('answers') or [])]
    slip_positions = [i for i, r in enumerate(slip_answers) if str(r).strip().lower()[:1] == 'y']
    left_shells = [i for i, v in enumerate(openings) if v == 'l']
    good = len(left_shells) == 1 and slip_positions == left_shells
    return {'state': 'marked' if good else 'astray', 'n': len(slip_answers), 'verdict': 'slip beside shell %s, the odd shell is %s' % (' '.join(str(i + 1) for i in slip_positions) or 'none', ' '.join(str(i + 1) for i in left_shells) or 'none')}

# end of code_slip_binding
