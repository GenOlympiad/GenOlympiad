# code: helpers
from genolympiad.task_helpers import pick_smallest_or_largest_figure
# end of helpers

# shared code: code_gauge
def num(node):
    got = (node or {}).get('answers') if isinstance(node, dict) else None
    raw = str((got or [''])[0]).strip().lower()
    if any(w in raw for w in ('none', 'blank', 'nil', 'empty', 'unknown', 'not ', 'cannot')):
        return ''
    d = ''.join(c for c in raw if c.isdigit())
    return (d.lstrip('0') or '0') if d else ''


def working_gauge_held(a, b, c, first, last):
    """Whether the working gauge stays the same in all photos while the contents gauge drops."""
    working = [num(a), num(b), num(c)]
    first_figure, last_figure = num(first), num(last)
    ok = all(working) and len(set(working)) == 1 and first_figure and last_figure and int(last_figure) < int(first_figure)
    return {'v': 'yes' if ok else 'no',
            'verdict': 'the working gauge reads %s while the contents gauge goes from %s to %s' % ('/'.join(x or 'nothing' for x in working), first_figure or 'nothing', last_figure or 'nothing')}


def contents_gauge_falls(a, b, c):
    """Whether the contents gauge band falls from photo to photo."""
    bands = [num(a), num(b), num(c)]
    ok = all(bands) and int(bands[0]) > int(bands[1]) > int(bands[2])
    return {'v': 'yes' if ok else 'no',
            'verdict': 'the contents gauge sits in bands %s'
            % '/'.join(x or 'nothing' for x in bands)}


def read_needle_figure(node):
    """The figure the needle reads in the last photo, or unreadable."""
    figure = num(node)
    return {'txt': figure or 'unreadable',
            'verdict': 'the needle in that photograph reads %s' % (figure or 'nothing')}

# end of code_gauge
