# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_ir_patches
def patch_colours_match(tag_reads, colour_reads, wanted):
    """Whether patches A, B and C show the expected thermal colours."""
    rows = {}
    for a, b in zip((tag_reads or {}).get('answers') or [], (colour_reads or {}).get('answers') or []):
        k = str(a).strip().upper()[:1]
        if k in ('A', 'B', 'C'):
            rows[k] = str(b).strip().lower()
    ok = all(rows.get(k, '').startswith(str(wanted[k])[:4]) for k in ('A', 'B', 'C'))
    return {'rows': rows, 'verdict': 'ranked' if ok else 'unranked',
            'note': 'the lettered patches came out %s' % sorted(rows.items())}

def probe_readings_agree(reads, tol):
    """Whether three or more contact probe readings agree within the allowed spread."""
    import re
    values = []
    for a in (reads or {}).get('answers') or []:
        m = re.search(r'-?\d+(?:\.\d+)?', str(a).replace(',', ''))
        if m:
            values.append(float(m.group()))
    span = (max(values) - min(values)) if values else -1.0
    ok = len(values) >= 3 and span <= float(tol)
    return {'vals': values, 'span': span, 'verdict': 'agree' if ok else 'disagree',
            'note': '%d contact readings spanning %s degrees' % (len(values), span)}

# end of code_ir_patches
