# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_listed_items
# end of helpers

# shared code: code_infill_record
def score_infill_record(key_read, band_read, cord_read, level_read, carry_read, fills_read, captions, band_wanted, cord_wanted, level_wanted, carry_wanted, fills_wanted):
    """Count the band, cord, level, carry and fill-count reads that match their wanted values."""
    def as_list(n):
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
    def num(v):
        d = ''.join(c for c in str(v) if c.isdigit())
        return int(d) if d and len(d) <= 3 else None
    def one(n):
        v = as_list(n)
        return v[0] if v else None
    def ival(v):
        try:
            return int(float(str(v)))
        except (TypeError, ValueError):
            return None
    want = [str(x) for x in as_list(captions)]
    band_targets, cord_targets = as_list(band_wanted), as_list(cord_wanted)
    got = align_by_printed_key([{'key': x, 'b': p, 'c': q}
                                for x, p, q in zip(as_list(key_read), as_list(band_read), as_list(cord_read))], want)
    n, notes = 0, []
    for i, row in enumerate(got):
        r = row if isinstance(row, dict) else {}
        band_got, cord_got = num(r.get('b')), num(r.get('c'))
        band_target = ival(band_targets[i]) if i < len(band_targets) else None
        cord_target = ival(cord_targets[i]) if i < len(cord_targets) else None
        if band_got is not None and band_target is not None and band_got == band_target:
            n += 1
        if cord_got is not None and cord_target is not None and cord_got == cord_target:
            n += 1
        notes.append('%s band %r wanted %r, cord %r wanted %r'
                   % (want[i] if i < len(want) else i, band_got, band_target, cord_got, cord_target))
    level_got = pick(one(level_read), ['below', 'level', 'proud'])
    if level_got is not None and level_got == str(level_wanted).lower():
        n += 1
    carry_got = pick(one(carry_read), ['yes', 'no'])
    if carry_got is not None and carry_got == str(carry_wanted).lower():
        n += 1
    fills_got, fills_target = num(one(fills_read)), ival(fills_wanted)
    if fills_got is not None and fills_target is not None and fills_got == fills_target:
        n += 1
    notes.append('fill sits %r, band carried across %r, %r fills' % (level_got, carry_got, fills_got))
    return {'n': n, 'checks': 2 * len(want) + 3, 'verdict': '; '.join(notes)}

# end of code_infill_record
