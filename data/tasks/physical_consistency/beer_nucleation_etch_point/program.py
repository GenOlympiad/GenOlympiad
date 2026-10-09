# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_key_matches
# end of helpers

# shared code: code_key_pair_frac
def match_pinned_states(keys, vals, want):
    """Score each pinned key on whether its read value contains the wanted state."""
    wanted = dict(p.split('=') for p in str(want).split('|') if p.count('=') == 1)
    key_answers = [str(a).strip().upper().replace(' ', '') for a in ((keys or {}).get('answers') or [])]
    value_answers = [str(a).strip().lower().replace('-', ' ') for a in ((vals or {}).get('answers') or [])]
    scores = {}
    for k, s in zip(key_answers, value_answers):
        wanted_state = str(wanted.get(k, '')).strip().lower()
        scores[k] = 1.0 if (wanted_state and s and wanted_state in s) else 0.0
    ordered_keys = sorted(wanted)
    return {'a': scores.get(ordered_keys[0], 0.0) if ordered_keys else 0.0, 'b': scores.get(ordered_keys[1], 0.0) if len(ordered_keys) > 1 else 0.0, 'c': scores.get(ordered_keys[2], 0.0) if len(ordered_keys) > 2 else 0.0, 'verdict': 'each pinned half of the conjunction reads %s' % sorted(scores.items())}

# end of code_key_pair_frac
