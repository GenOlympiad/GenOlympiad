# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# shared code: code_a575382b6706

def fold_die_net(faces, pips, reference):
    """Fold the cross net and test that opposite faces sum to 7 with the right handedness."""
    import re as _re
    g = (faces or {}).get('geometry') or []
    answers = (pips or {}).get('answers') or []
    out = {'no_cross_topology': 1, 'not_all_six_read': 1, 'valid_die': False,
           'valid_yn': 'no', 'n_pairs_ok': 0, 'all_present': False,
           'handed': None, 'layout': None, 'values': None}
    if len(g) != 6 or len(answers) < 6:
        return out
    centres = [((float(b[0]) + float(b[2])) / 2.0, (float(b[1]) + float(b[3])) / 2.0) for b in g]
    widths = sorted(abs(float(b[3]) - float(b[1])) for b in g)
    heights = sorted(abs(float(b[2]) - float(b[0])) for b in g)
    sw, sh = widths[len(widths) // 2], heights[len(heights) // 2]
    if sw <= 0 or sh <= 0:
        return out
    order = sorted(range(6), key=lambda k: centres[k][1])
    groups, cur = [], [order[0]]
    for k in order[1:]:
        if abs(centres[k][1] - centres[cur[-1]][1]) <= 0.45 * sw:
            cur.append(k)
        else:
            groups.append(cur); cur = [k]
    groups.append(cur)
    if [len(x) for x in groups] != [1, 4, 1]:
        return out
    left, col, right = groups[0][0], groups[1], groups[2][0]
    col = sorted(col, key=lambda k: centres[k][0])
    r0, r1, r2, r3 = col
    if abs(centres[left][0] - centres[r1][0]) > 0.5 * sh or abs(centres[right][0] - centres[r1][0]) > 0.5 * sh:
        return out
    out['no_cross_topology'] = 0
    idx = {'r0': r0, 'r1': r1, 'r2': r2, 'r3': r3, 'L': left, 'R': right}

    def val(s):
        m = _re.findall(r'\d+', str(s or ''))
        if not m:
            return None
        v = int(m[-1])
        return v if 1 <= v <= 6 else None
    v = {k: val(answers[i]) for k, i in idx.items()}
    if any(v[k] is None for k in v):
        return out
    out['not_all_six_read'] = 0
    out['values'] = {k: v[k] for k in v}
    out['layout'] = {k: [round(centres[i][0], 1), round(centres[i][1], 1)] for k, i in idx.items()}

    N = {'r1': (0, 0, 1), 'r0': (0, 1, 0), 'r2': (0, -1, 0), 'r3': (0, 0, -1),
         'L': (-1, 0, 0), 'R': (1, 0, 0)}
    pairs = [('r0', 'r2'), ('r1', 'r3'), ('L', 'R')]
    out['n_pairs_ok'] = sum(1 for a, b in pairs if v[a] + v[b] == 7)
    out['all_present'] = sorted(v.values()) == [1, 2, 3, 4, 5, 6]
    if out['all_present']:
        inv = {v[k]: N[k] for k in v}
        n1, n2, n3 = inv[1], inv[2], inv[3]
        cr = (n2[1] * n3[2] - n2[2] * n3[1],
              n2[2] * n3[0] - n2[0] * n3[2],
              n2[0] * n3[1] - n2[1] * n3[0])
        found_boxes = n1[0] * cr[0] + n1[1] * cr[1] + n1[2] * cr[2]
        out['handed'] = 'western' if found_boxes > 0 else ('eastern' if found_boxes < 0 else None)
    want = str(reference.get('require_chirality') or '').strip().lower()
    ok = bool(out['all_present']) and out['n_pairs_ok'] == 3
    if want:
        ok = ok and (out['handed'] == want)
    out['valid_die'] = bool(ok)
    out['valid_yn'] = 'yes' if ok else 'no'
    return out

# end of code_a575382b6706
