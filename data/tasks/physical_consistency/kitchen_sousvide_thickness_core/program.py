# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: code_probe
def core_temps_by_thickness(reads, thicknesses, target):
    """Read the core temperature for each thickness and say if it reaches the target."""
    import re
    temp_by_thickness = {}
    for a in (reads or {}).get('answers') or []:
        numbers = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', str(a))]
        if len(numbers) >= 2:
            temp_by_thickness[int(round(numbers[-2]))] = numbers[-1]
    temps = [temp_by_thickness.get(int(t)) for t in thicknesses]
    side = [('none' if v is None else ('at' if v >= float(target) else 'below')) for v in temps]
    rank = [str(int(t)) for _, t in sorted(zip([-99.0 if v is None else v for v in temps], [float(t) for t in thicknesses]), reverse=True)]
    return {'seq': temps, 'side': [side], 'rank': rank, 'n_read': sum(1 for v in temps if v is not None), 'verdict': 'core temperature by thickness %s mm = %s degC, which is %s the %s degC the docket works to; hottest first %s' % (thicknesses, temps, side, target, rank)}

# end of code_probe

# code: code_tieout
def strip_and_faces_agree(probe_result, face_result):
    """Agree when each thickness at target has an even face and each one below a middle face."""
    face_for_side = {'at': 'even', 'below': 'middle'}
    sides = ((probe_result or {}).get('side') or [[]])[0]
    row = (face_result or {}).get('row') or []
    n = min(len(sides), len(row))
    hits = sum(1 for i in range(n) if face_for_side.get(sides[i]) == row[i])
    ok = n > 0 and hits == n and len(sides) == len(row)
    return {'sides': sides, 'row': row, 'n_agree': hits,
            'verdict': 'agree' if ok else 'disagree',
            'note': 'the strip says %s and the cut faces say %s' % (sides, row)}

# end of code_tieout

# code: code_faces
def cut_faces_by_thickness(keys, node, thicknesses):
    """Read the cut-face look for each thickness from the labelled cut-outs."""
    import re
    key_digits = [re.findall(r'\d+', str(x)) for x in ((keys or {}).get('answers') or [])]
    face_words = [(str(x).strip().lower().strip('.,;:').split() or ['none'])[0] for x in ((node or {}).get('answers') or [])]
    face_by_thickness = {}
    for i, k in enumerate(key_digits):
        if k and i < len(face_words):
            face_by_thickness[int(k[-1])] = face_words[i]
    row = [face_by_thickness.get(int(t), 'none') for t in thicknesses]
    return {'rows': [row], 'row': row, 'n': sum(1 for v in row if v != 'none'), 'verdict': 'cut face by thickness %s mm -> %s' % (thicknesses, row)}

# end of code_faces
