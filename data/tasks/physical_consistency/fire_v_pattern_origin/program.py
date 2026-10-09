# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_key_matches
# end of helpers

# shared code: code_key_pair_frac
def rod_lean_scores(keys, vals, rods, grille, want):
    """Score each rod mark: even where wanted, else leaning to the grille's side."""
    wanted = dict(p.split('=') for p in str(want).split('|') if p.count('=') == 1)
    key_answers = [str(a).strip().upper().replace(' ', '') for a in ((keys or {}).get('answers') or [])]
    value_answers = [str(a).strip().lower().replace('-', ' ') for a in ((vals or {}).get('answers') or [])]
    def boxes_of(n):
        g = (n or {}).get('geometry') if isinstance(n, dict) else None
        return [b for b in (g or []) if isinstance(b, (list, tuple)) and len(b) >= 4]
    rod_boxes, grille_boxes = boxes_of(rods), boxes_of(grille)
    grille_centre = (float(grille_boxes[0][0]) + float(grille_boxes[0][2])) / 2.0 if grille_boxes else None
    scores, notes = {}, []
    for i, (k, s) in enumerate(zip(key_answers, value_answers)):
        wanted_state = str(wanted.get(k, '')).strip().lower()
        if not wanted_state or not s:
            scores[k] = 0.0
            notes.append('rod %s could not be read' % (k or '?'))
            continue
        if 'even' in wanted_state:
            scores[k] = 1.0 if ('even' in s and 'lean' not in s) else 0.0
            notes.append('rod %s wants a mark standing even and reads %r' % (k, s))
        elif grille_centre is None or i >= len(rod_boxes):
            scores[k] = 0.0
            notes.append('rod %s: the grille or the rod box was not read, so the lean cannot '
                       'be judged' % k)
        else:
            rod_centre = (float(rod_boxes[i][0]) + float(rod_boxes[i][2])) / 2.0
            side = 'left' if grille_centre < rod_centre else 'right'
            scores[k] = 1.0 if (side in s and 'even' not in s) else 0.0
            notes.append('rod %s: the grille hangs to the %s of this rod on the page and the '
                       'mark reads %r' % (k, side, s))
    ordered_keys = sorted(wanted)
    return {'a': scores.get(ordered_keys[0], 0.0) if ordered_keys else 0.0,
            'b': scores.get(ordered_keys[1], 0.0) if len(ordered_keys) > 1 else 0.0,
            'verdict': '; '.join(notes)}

# end of code_key_pair_frac
