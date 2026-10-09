# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_feature_seq
def station_yes_no_sequence(reads):
    """The yes or no answer for each station, left to right, joined into one string."""
    answers = [str(x).strip().lower() for x in (reads or {}).get('answers') or []]
    s = '|'.join('yes' if t.startswith('y') else 'no' for t in answers)
    return {'seq': s, 'n': len(answers),
            'verdict': 'per-station answers left to right read as %s' % (s or 'nothing')}

# end of code_feature_seq
