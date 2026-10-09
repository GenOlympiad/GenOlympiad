# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: turnround_code
def check_row_end_numbers(keys, ends, lefts, rights, want):
    """Whether every row shows the expected tooth numbers at its outer end and centre line."""
    wanted = dict(p.split('=') for p in str(want).split(',') if p.count('=') == 1)
    keys_read = [str(a).strip().upper() for a in ((keys or {}).get('answers') or [])]
    number_reads = [[str(a).strip() for a in ((n or {}).get('answers') or [])]
           for n in (ends, lefts, rights)]
    numbers_by_key = dict((k, [t[i] if i < len(t) else '' for t in number_reads]) for i, k in enumerate(keys_read))
    n = sum(1 for k in wanted if numbers_by_key.get(k) == [x.strip() for x in wanted[k].split('|')])
    return {'ok': 'yes' if wanted and n == len(wanted) else 'no', 'n': n,
            'verdict': '%d of the %d rows carry the numbers the notation puts at their outer end and on either side of the centre line' % (n, len(wanted))}

# end of turnround_code

# code: marked_teeth_code
def check_marked_teeth(keys, shades, want):
    """Whether every row carries its crown mark on the tooth the note names, with the count."""
    wanted = dict(p.split('=') for p in str(want).split(',') if p.count('=') == 1)
    keys_read = [str(a).strip().upper() for a in ((keys or {}).get('answers') or [])]
    shades_read = [str(a).strip() for a in ((shades or {}).get('answers') or [])]
    shade_by_key = dict(zip(keys_read, shades_read))
    n = sum(1 for k in wanted if shade_by_key.get(k, '') == wanted[k].strip())
    return {'ok': 'yes' if wanted and n == len(wanted) else 'no', 'n': n,
            'verdict': '%d of the %d rows carry their crown mark on the tooth the surgery note names' % (n, len(wanted))}

# end of marked_teeth_code
