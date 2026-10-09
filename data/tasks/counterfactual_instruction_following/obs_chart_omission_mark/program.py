# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_ordvec
def read_run_in_order(node):
    """The cut-outs along the run read in page order, or refuse if none was read."""
    reads = []
    for raw in (node or {}).get('answers') or []:
        t = ' '.join(str(raw or '').lower().split())
        t = ''.join(c for c in t if c.isalnum() or c in ' .-').strip()
        reads.append(t or 'unread')
    if not reads or all(t == 'unread' for t in reads):
        return {'seq': 'no reading', 'refused': True,
                'verdict': 'no cut-out along the run came back with an answer -> abstain'}
    return {'seq': '|'.join(reads), 'n': len(reads),
            'verdict': 'read in page order: ' + ' | '.join(reads)}

# end of code_ordvec

# shared code: code_onefig
def read_first_figure(node):
    """The first figure read in the cut-out, or refuse if there is none."""
    for raw in (node or {}).get('answers') or []:
        t = ''.join(c for c in str(raw) if c.isdigit() or c == '.')
        if '.' in t:
            t = t.rstrip('0').rstrip('.')
        if t:
            return {'v': t, 'verdict': 'the cut-out reads the figure %s' % t}
    return {'v': 'no reading', 'refused': True,
            'verdict': 'no figure was read out of the cut-out -> abstain'}

# end of code_onefig
