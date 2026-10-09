# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, map_answer_to_token
# end of helpers

# shared code: code_over
def overhang_pattern_matches(keys, past, want):
    """Check that each numbered block's read overhang state matches the reference pattern."""
    block_numbers = [''.join(c for c in str(k) if c.isdigit())
          for k in (keys or {}).get('answers') or []]
    past_states = [str(p).strip().lower()[:1] for p in (past or {}).get('answers') or []]
    expected = dict(p.split(':') for p in str(want).split(','))
    got = {block_numbers[i]: past_states[i] for i in range(min(len(block_numbers), len(past_states)))}
    matches = len(got) == len(expected) and all(got.get(k) == v for k, v in expected.items())
    return {'state': 'match' if matches else 'off', 'n': len(got),
            'verdict': '; '.join('%s=%s' % (k, got[k]) for k in sorted(got))
                       or 'nothing read'}

# end of code_over

# shared code: code_flat
def count_level_blocks(node, want):
    """Check that every block in the stack reads as lying level."""
    answers = [str(a).strip().lower()[:1] for a in (node or {}).get('answers') or []]
    level_count = sum(1 for a in answers if a == 'y')
    matches = len(answers) == int(want) and level_count == int(want)
    return {'state': 'match' if matches else 'off', 'n': level_count,
            'verdict': '%d of %d blocks lie level' % (level_count, len(answers))}

# end of code_flat
