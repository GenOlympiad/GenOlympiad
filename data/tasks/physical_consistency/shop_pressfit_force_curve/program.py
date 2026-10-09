# shared code: code_curve_rows
def describe_curves(cert, ser, win, box, rise):
    """Describe each confirmed curve by serial, window crossing and whether force climbs."""
    def toks(s):
        return ''.join(c if c.isalpha() else ' ' for c in str(s).lower()).split()
    def code(s):
        return ''.join(c for c in str(s).lower() if c.isalnum())
    confirms = [str(a) for a in (cert or {}).get('answers') or []]
    serials = [str(a) for a in (ser or {}).get('answers') or []]
    window_reads = [str(a) for a in (win or {}).get('answers') or []]
    box_reads = [str(a) for a in (box or {}).get('answers') or []]
    rise_reads = [str(a) for a in (rise or {}).get('answers') or []]
    rows = []
    for i, c in enumerate(confirms):
        if 'yes' not in toks(c):
            continue
        k = code(serials[i]) if i < len(serials) else ''
        wt = toks(window_reads[i]) if i < len(window_reads) else []
        bt = toks(box_reads[i]) if i < len(box_reads) else []
        rt = toks(rise_reads[i]) if i < len(rise_reads) else []
        if not k:
            rows.append('unread curve')
            continue
        if 'yes' in wt:
            where = 'through' if 'yes' in bt else ('outside' if 'no' in bt else 'unread')
        elif 'no' in wt:
            where = 'nowindow'
        else:
            where = 'unread'
        if 'climbs' in rt:
            how = 'climbs'
        elif 'stays' in rt:
            how = 'stays'
        else:
            how = 'unread'
        rows.append('%s %s %s' % (k, where, how))
    seq = ', '.join(sorted(set(rows)))
    return {'seq': seq, 'n': len(set(rows)),
            'verdict': 'the recorded curves read as: %s' % (seq or 'nothing')}

# end of code_curve_rows

# shared code: code_pair_set
def read_seat_states(cert, keys, vals):
    """List each confirmed part's serial with whether it sits flush or proud."""
    def toks(s):
        return ''.join(c if c.isalpha() else ' ' for c in str(s).lower()).split()
    def code(s):
        return ''.join(c for c in str(s).lower() if c.isalnum())
    confirms = [str(a) for a in (cert or {}).get('answers') or []]
    serials = [str(a) for a in (keys or {}).get('answers') or []]
    seat_reads = [str(a) for a in (vals or {}).get('answers') or []]
    rows = []
    for i, c in enumerate(confirms):
        if 'yes' not in toks(c):
            continue
        k = code(serials[i]) if i < len(serials) else ''
        t = toks(seat_reads[i]) if i < len(seat_reads) else []
        if 'flush' in t:
            v = 'flush'
        elif 'proud' in t:
            v = 'proud'
        else:
            v = 'unread'
        rows.append('%s %s' % (k or 'unread', v))
    seq = ', '.join(sorted(set(rows)))
    return {'seq': seq, 'n': len(set(rows)),
            'verdict': 'the parts on the bench read as: %s' % (seq or 'nothing')}

# end of code_pair_set
