# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: sub_fit_code
def count_subtitle_places(node, want):
    """Count the subtitle positions read that match the required placement, in frame order."""
    reads = [str(a).strip().lower() for a in ((node or {}).get('answers') or [])]
    wanted = [str(x).strip().lower() for x in (want or [])]
    n = 0
    for s, t in zip(reads, wanted):
        n += 1 if (t and s and s.startswith(t)) else 0
    return {'n': n, 'read': len(reads), 'verdict': '%d of the %d places read as the record requires' % (n, len(wanted))}

# end of sub_fit_code

# code: cap_fit_code
def count_caption_places(node, want):
    """Count the caption strap positions read that match the required placement, in frame order."""
    reads = [str(a).strip().lower() for a in ((node or {}).get('answers') or [])]
    wanted = [str(x).strip().lower() for x in (want or [])]
    n = 0
    for s, t in zip(reads, wanted):
        n += 1 if (t and s and s.startswith(t)) else 0
    return {'n': n, 'read': len(reads), 'verdict': '%d of the %d places read as the record requires' % (n, len(wanted))}

# end of cap_fit_code
