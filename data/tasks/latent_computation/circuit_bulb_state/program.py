# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_7c11890e93d0
def read_lamps(box, node):
    """Read each lamp as lit or unlit, ordered from left to right."""
    geometry = (box or {}).get('geometry') or []
    answers = (node or {}).get('answers') or []
    if not geometry or len(answers) != len(geometry):
        return {'states': None, 'n': 0, 'unreadable': True}
    order = sorted(range(len(geometry)), key=lambda i: (float(geometry[i][1]) + float(geometry[i][3])) / 2.0)
    states = []
    for i in order:
        a = str(answers[i] or '').strip().lower()
        if 'unlit' in a or a.startswith('dark') or a.startswith('off'):
            states.append(False)
        elif a.startswith('lit') or a.startswith('on') or 'glow' in a or 'bright' in a:
            states.append(True)
        else:
            states.append(None)
    if any(v is None for v in states):
        return {'states': None, 'n': len(states), 'unreadable': True}
    return {'states': states, 'n': len(states), 'unreadable': False}

def score_joint(reads, target):
    """1.0 only if every lamp state matches the reference."""
    target_states = [bool(x) for x in (target or [])]
    read_states = (reads or {}).get('states')
    if not read_states or len(read_states) != len(target_states):
        return {'frac': 0.0, 'got': read_states, 'want': target_states}
    ok = all(a == b for a, b in zip(read_states, target_states))
    return {'frac': 1.0 if ok else 0.0, 'got': read_states, 'want': target_states}

def score_partial(reads, target):
    """The share of lamps whose state matches the reference."""
    target_states = [bool(x) for x in (target or [])]
    read_states = (reads or {}).get('states') or []
    if not target_states:
        return {'frac': 0.0, 'got': read_states, 'want': target_states}
    n_match = sum(1 for i, b in enumerate(target_states) if i < len(read_states) and read_states[i] == b)
    return {'frac': round(n_match / len(target_states), 4), 'got': read_states, 'want': target_states}

# end of code_7c11890e93d0

# code: hold_joint_code
def hold_joint(reads):
    """Withhold the lamp reading when it could not be read."""
    result = dict(reads) if isinstance(reads, dict) else {'states': None, 'n': 0, 'unreadable': True}
    if result.get('unreadable'):
        result['refused'] = True
    return result

# end of hold_joint_code

# code: hold_partial_code
def hold_partial(reads):
    """Withhold the lamp reading when it could not be read."""
    result = dict(reads) if isinstance(reads, dict) else {'states': None, 'n': 0, 'unreadable': True}
    if result.get('unreadable'):
        result['refused'] = True
    return result

# end of hold_partial_code

# code: not_all_code
def not_all_confirmed(node):
    """1.0 when at least one cutout answer is not a yes."""
    answers = (node or {}).get('answers') or []
    n = sum(1 for a in answers if str(a).strip().lower().startswith('y'))
    return 1.0 if (answers and n < len(answers)) else 0.0

# end of not_all_code

# code: absence_code
def marks_absent(sweep):
    """Whether the picture is free of printed marks, given the vetted count and allowance."""
    if not isinstance(sweep, dict): return {'clean': None, 'no_read': True, 'refused': True, 'verdict': 'the sweep returned no result'}
    n = sweep.get('n_confirmed')
    allow = sweep.get('allow')
    allow = 0 if allow is None else int(allow)
    if n is None: return {'clean': None, 'no_read': True, 'refused': True, 'verdict': 'the sweep reported no vetted count'}
    n = int(n)
    if n > allow: return {'clean': 'no', 'no_read': False, 'n_confirmed': n, 'allow': allow, 'verdict': '%d printed mark(s) were individually vetted in their own cut-outs (allowance %d), so the picture is not free of printed marks whether or not the sweep found every one' % (n, allow)}
    if sweep.get('refused'): return {'clean': None, 'no_read': True, 'refused': True, 'n_confirmed': n, 'allow': allow, 'verdict': 'nothing was vetted and the completeness ring could not certify the picture is clean'}
    return {'clean': sweep.get('clean') or 'yes', 'no_read': False, 'n_confirmed': n, 'allow': allow, 'verdict': 'the sweep certified %d vetted mark(s) (allowance %d)' % (n, allow)}

# end of absence_code
