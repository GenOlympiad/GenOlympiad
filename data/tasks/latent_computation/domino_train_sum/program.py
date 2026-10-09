# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_listed_items
# end of helpers

# shared code: code_84359481bb32
def tally_pips_and_joints(first_reads, second_reads, halves):
    """Total the pips read and count joints where touching halves show equal pips."""
    import re
    A = (first_reads or {}).get('answers') or []
    B = (second_reads or {}).get('answers') or []
    n = min(len(A), len(B))

    def pip(a):
        m = re.search(r'\d+', str(a))
        v = int(m.group()) if m else None
        return v if (v is not None and 0 <= v <= 6) else None

    faces = [[pip(A[i]), pip(B[i])] for i in range(n)]
    kept = [v for f in faces for v in f if v is not None]

    def walk(forward):
        ok = 0
        ver = 0
        for i in range(len(faces) - 1):
            a, b = ((faces[i][1], faces[i + 1][0]) if forward
                    else (faces[i][0], faces[i + 1][1]))
            if a is None or b is None:
                continue
            ver += 1
            ok += 1 if a == b else 0
        return ok, ver

    okA, verA = walk(True)
    n_ok, n_ver, sense = okA, verA, 'trailing->leading'
    if (halves or {}).get('across'):
        okB, verB = walk(False)
        if okB > okA:
            n_ok, n_ver, sense = okB, verB, 'leading->trailing (quarter-turn)'
    return {'total': sum(kept), 'n_tiles': len(faces), 'faces': faces,
            'n_ok': n_ok, 'n_ver': n_ver, 'sense': sense,
            'frac': (n_ok / float(n_ver)) if n_ver else None,
            'exhausted': n_ver == 0}

# end of code_84359481bb32

# shared code: code_216f066d9914
def split_tile_halves(boxes, divider_text):
    """Split each tile box into two halves, across or along, ordered left to right."""
    tile_boxes = list((boxes or {}).get('geometry') or [])
    tile_boxes.sort(key=lambda b: (b[1] + b[3]) / 2.0)
    s = str(divider_text or '').strip().lower()
    across = ('across' in s) or ('horizontal' in s) or ('upper' in s)
    first, second = [], []
    for b in tile_boxes:
        y0, x0, y1, x1 = float(b[0]), float(b[1]), float(b[2]), float(b[3])
        if across:
            m = (y0 + y1) / 2.0
            first.append([y0, x0, m, x1])
            second.append([m, x0, y1, x1])
        else:
            m = (x0 + x1) / 2.0
            first.append([y0, x0, y1, m])
            second.append([y0, m, y1, x1])
    return {'across': across, 'n': len(tile_boxes),
            'first': {'geometry': first}, 'second': {'geometry': second}}

# end of code_216f066d9914

# code: hold_chain_match_dp2_code
def refuse_if_no_joints(tally):
    """Refuse when no joint between tiles could be checked."""
    h = bool((tally or {}).get('exhausted'))
    return {'exhausted': h, 'refused': h}

# end of hold_chain_match_dp2_code

# code: hold_d1_joints_match_dp3_code
def refuse_if_no_joints(tally):
    """Refuse when no joint between tiles could be checked."""
    h = bool((tally or {}).get('exhausted'))
    return {'exhausted': h, 'refused': h}

# end of hold_d1_joints_match_dp3_code

# code: all_joints_match_code
def all_joints_match(tally):
    """1 if every checked joint shows equal pips on both sides, else 0."""
    d = tally or {}
    n_ver = d.get('n_ver') or 0
    if not n_ver:
        return 0.0
    return 1.0 if d.get('n_ok') == n_ver else 0.0

# end of all_joints_match_code
