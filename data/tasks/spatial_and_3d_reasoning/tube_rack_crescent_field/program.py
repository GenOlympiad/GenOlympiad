# code: helpers
from genolympiad.task_helpers import (
    count_confirmed_cutouts, paint_cells_by_fraction, plan_pinned_grid)
# end of helpers

# shared code: code_bore_row
def bore_row(node):
    """The bore shape seen in each pipe, as a one line grid of full circle, left or right."""
    shapes = []
    for a in ((node or {}).get('answers') or []):
        s = str(a).strip().lower()
        shapes.append('round' if 'round' in s else 'left' if 'left' in s
                 else 'right' if 'right' in s else '?')
    return [shapes]

# end of code_bore_row

# shared code: code_one_flip
def check_single_flip(node, axis_index):
    """Check the crescents change side once and the only full circle is the on axis pipe."""
    shapes = []
    for a in ((node or {}).get('answers') or []):
        s = str(a).strip().lower()
        shapes.append('round' if 'round' in s else 'left' if 'left' in s
                 else 'right' if 'right' in s else '?')
    sides = [x for x in shapes if x in ('left', 'right')]
    flips = sum(1 for i in range(len(sides) - 1) if sides[i] != sides[i + 1])
    ring = [i + 1 for i, x in enumerate(shapes) if x == 'round']
    ok = 'yes' if flips == 1 and ring == [int(axis_index)] and '?' not in shapes else 'no'
    return {'ok': ok, 'flips': flips, 'ring_at': ring, 'n': len(shapes), 'row': shapes,
            'verdict': '%d changes of side along the cradle, full ring at %s' % (flips, ring)}

# end of code_one_flip
