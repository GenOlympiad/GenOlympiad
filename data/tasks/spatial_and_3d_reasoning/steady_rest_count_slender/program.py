# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_flag_set
def flagged_band_numbers(labels, flags):
    """The sorted band numbers whose cut-outs were confirmed as carrying a steady rest."""
    band_numbers = [''.join(str(a).lower().split()).strip('.,:') for a in ((labels or {}).get('answers') or [])]
    flagged = [str(b).strip().lower().startswith('y') for b in ((flags or {}).get('answers') or [])]
    hits = []
    for i, n in enumerate(band_numbers):
        if n and i < len(flagged) and flagged[i]:
            hits.append(n)
    seq = ', '.join(sorted(set(hits)))
    return {'seq': seq, 'verdict': 'flagged references: %s' % (seq or 'none')}

# end of code_flag_set
