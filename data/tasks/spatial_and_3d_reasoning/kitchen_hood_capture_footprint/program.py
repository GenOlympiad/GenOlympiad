# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_hood_cover
def hood_cover_checks(unit_keys, front_reads, back_read, ends_read, unit_order, front_want, back_want, ends_want):
    """Count the canopy front, back and end readings that match the reference positions."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def pick(v, opts):
        if v is None:
            return None
        s = ' '.join(str(v).lower().replace('-', ' ').split())
        if s in ('', 'none', 'n a', 'na', 'nil', 'empty', '?', '.'):
            return None
        for o in opts:
            if o in s:
                return o
        return None
    def one(n):
        v = lst(n)
        return v[0] if v else None
    units = [str(x) for x in lst(unit_order)]
    readings_by_unit = align_by_printed_key([{'key': x, 'f': v} for x, v in zip(lst(unit_keys), lst(front_reads))], units)
    n, notes = 0, []
    for i, row in enumerate(readings_by_unit):
        r = row if isinstance(row, dict) else {}
        p = pick(r.get('f'), ['in front of', 'level with', 'behind'])
        if p is not None and p == str(front_want).lower():
            n += 1
        notes.append('%s canopy edge %r' % (units[i] if i < len(units) else i, p))
    back_position = pick(one(back_read), ['flush against the wall', 'standing away from the wall'])
    if back_position is not None and back_position == str(back_want).lower():
        n += 1
    overhangs_ends = pick(one(ends_read), ['yes', 'no'])
    if overhangs_ends is not None and overhangs_ends == str(ends_want).lower():
        n += 1
    notes.append('back edge %r, overhangs both ends %r' % (back_position, overhangs_ends))
    return {'n': n, 'checks': len(units) + 2, 'verdict': '; '.join(notes)}

# end of code_hood_cover
