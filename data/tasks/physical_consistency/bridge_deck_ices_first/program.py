# shared code: code_label_set
def frosted_post_chainages(labels, flags, want_n):
    """List the chainages of the posts read as standing beside frosted road."""
    digits = ''.join(ch for ch in str(want_n) if ch.isdigit())
    want = int(digits) if digits else 0
    chainages = [''.join(str(a).lower().split()).strip('.,:') for a in ((labels or {}).get('answers') or [])]
    frost_flags = [str(b).strip().lower()[:1] for b in ((flags or {}).get('answers') or [])]
    if len(chainages) != want or len(frost_flags) != want or not all(chainages) or not all(f in ('y', 'n') for f in frost_flags):
        return {'unreadable': True, 'seq': '', 'verdict': 'the verge posts did not all come back with a chainage and a plain yes or no -> honest refusal'}
    frosted = sorted(set(n for i, n in enumerate(chainages) if frost_flags[i] == 'y'))
    return {'unreadable': False, 'seq': ', '.join(frosted), 'verdict': 'the posts standing beside frosted road read: %s' % (', '.join(frosted) or 'none')}

# end of code_label_set

# shared code: code_joints
def frost_one_side_at_joints(cert, sides, want_n):
    """Check that frost lies on one side only at every confirmed expansion joint."""
    digits = ''.join(ch for ch in str(want_n) if ch.isdigit())
    want = int(digits) if digits else 0
    confirmed = [str(y).strip().lower().startswith('y') for y in ((cert or {}).get('answers') or [])]
    side_reads = [str(x).strip().lower() for x in ((sides or {}).get('answers') or [])]
    if len(confirmed) != want or len(side_reads) != want or not all(confirmed):
        return {'unreadable': True, 'ok': 'no', 'verdict': 'the two steel joints were not both confirmed and read -> honest refusal'}
    frost_sides = ['one' if 'one' in s else ('both' if 'both' in s else ('neither' if 'neither' in s else '')) for s in side_reads]
    if not all(frost_sides):
        return {'unreadable': True, 'ok': 'no', 'verdict': 'a joint did not say which side of it the frost lies on -> honest refusal'}
    return {'unreadable': False, 'ok': 'yes' if all(g == 'one' for g in frost_sides) else 'no', 'verdict': 'at the steel joints the frost lies on %s' % ', '.join(frost_sides)}

# end of code_joints
