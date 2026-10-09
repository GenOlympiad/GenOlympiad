# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, labelled_pairs
# end of helpers

# shared code: code_plate_map
def read_plate_sizes(plate_reads):
    """List the go and no-go sizes read from the gauge end plates."""
    import re
    rows = []
    for raw in (plate_reads or {}).get('answers') or []:
        txt = str(raw).lower().replace('-', ' ')
        word = 'nogo' if 'no' in txt else ('go' if 'go' in txt else '')
        m = re.search(r'\d+\.\d+', txt)
        if word and m:
            rows.append('%s:%s' % (word, m.group(0)))
    seq = ' '.join(sorted(set(rows)))
    return {'seq': seq or 'nothing read', 'n': len(rows), 'verdict': 'the end plates read %s' % (seq or 'none')}

# end of code_plate_map
