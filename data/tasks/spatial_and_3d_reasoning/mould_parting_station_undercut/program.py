# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_one_label
def parting_label_matches(reads, want):
    """Whether exactly one station label was read and it is the parting station."""
    labels = [str(a).strip().upper().replace(' ', '')
           for a in (reads or {}).get('answers') or []]
    wanted = str(want).strip().upper().replace(' ', '')
    ok = len(labels) == 1 and labels[0] == wanted
    return {'state': 'match' if ok else 'off', 'n': len(labels),
            'verdict': 'read %s, wanted %s' % ('|'.join(labels) or 'nothing', wanted)}

# end of code_one_label

# shared code: code_hatch
def hatched_stations_match(reads, want):
    """Whether the hatched stations read are exactly the undercut stations."""
    hatched = sorted(str(a).strip().upper().replace(' ', '')
                 for a in (reads or {}).get('answers') or [])
    wanted = sorted(w.strip().upper() for w in str(want).split(','))
    return {'state': 'match' if hatched == wanted else 'off', 'n': len(hatched),
            'verdict': 'hatching stands at %s' % (' '.join(hatched) or 'nothing')}

# end of code_hatch
