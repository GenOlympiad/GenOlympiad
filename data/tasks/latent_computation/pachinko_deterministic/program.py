# code: slot_law_code
def slot_score(ans, reference):
    """Score 1 when the slot number read equals the reference slot."""
    s = str(ans).strip().lower()
    if 'none' in s:
        return {'frac': 0.0, 'slot': None, 'no_read': True}
    numbers = ''.join(c if c.isdigit() else ' ' for c in s).split()
    if not numbers:
        return {'frac': 0.0, 'slot': None, 'no_read': True}
    slot = int(numbers[-1])
    if slot < 0 or slot >= int(reference['n_slots']):
        return {'frac': 0.0, 'slot': slot, 'no_read': True}
    return {'frac': 1.0 if slot == int(reference['gt_slot']) else 0.0, 'slot': slot, 'no_read': False}

# end of slot_law_code
