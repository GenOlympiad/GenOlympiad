# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_samechild
def same_child_name(label_read, script_read):
    """Whether the sachet label and the prescription give the same child's name."""
    def clean(n):
        v = n.get('answers') if isinstance(n, dict) else None
        v = list(v) if isinstance(v, (list, tuple)) else []
        s = str(v[0] if v else '').strip().lower()
        s = ' '.join(s.split())
        return '' if s in ('none', 'null', 'nil', 'n/a', 'na', 'empty', '?', '.', '-') else s
    label, script = clean(label_read), clean(script_read)
    return {'same': 'yes' if label and script and label == script else 'no', 'label': label, 'script': script,
            'verdict': 'sachet label says %r, prescription says %r' % (label, script)}

# end of code_samechild

# code: shapes_code
def count_tablet_pieces(shape_reads):
    """Count the whole and part tablets read on the sachet."""
    answers = [str(x).strip().lower() for x in (shape_reads or {}).get('answers') or []]
    n_whole = sum(1 for t in answers if t.startswith('whole'))
    n_part = sum(1 for t in answers if t.startswith('part') or t.startswith('half'))
    return {'pieces': 'whole:%d|part:%d' % (n_whole, n_part), 'whole': n_whole, 'part': n_part,
            'verdict': '%d whole tablets and %d part tablets on the sachet' % (n_whole, n_part)}

# end of shapes_code
