# code: helpers
from genolympiad.task_helpers import count_items_per_label
# end of helpers

# shared code: code_fb380c0e39c4
import re
def sum_row_counts(seq):
    """Add up the one number read for each row, refusing if fewer than two rows are listed."""
    s = str(seq if seq is not None else "")
    s = re.sub(r"\([^)]*\)", " ", s)
    parts = [p.strip() for p in re.split(r"[,;\n]+", s) if p.strip()]
    rows = []
    for p in parts:
        figures = re.findall(r"\d+", p)
        if len(figures) != 1:
            return {'total': -1, 'n_rows': 0, 'no_read': True, 'refused': True,
                    'why': 'a row entry did not carry exactly one figure: %r' % (p,)}
        rows.append(int(figures[0]))
    if len(rows) < 2:
        return {'total': -1, 'n_rows': len(rows), 'no_read': True, 'refused': True,
                'why': 'the reader gave no per-row list (a single figure is the whole-pile guess)'}
    return {'total': sum(rows), 'n_rows': len(rows), 'rows': rows, 'no_read': False}

# end of code_fb380c0e39c4
