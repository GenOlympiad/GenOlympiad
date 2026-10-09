# code: packing_code
def check_gap_packing(confirms, fill_reads):
    """Whether the 13 seats hold the four orders in whole blocks with grey seats between them."""
    import itertools
    pairs = zip((fill_reads or {}).get('answers') or [], (confirms or {}).get('answers') or [])
    fills = [str(t).strip().lower().rstrip('.') for t, y in pairs if str(y).strip().lower().startswith('y')]
    fills = ['grey' if v == 'gray' else v for v in fills]
    if len(fills) != 13:
        return {'canon': '%d certified seats' % len(fills), 'verdict': 'expected 13 certified seat icons in the row, the ring certified %d' % len(fills)}
    runs = [(c, len(list(g))) for c, g in itertools.groupby(fills)]
    blocks = [(c, n) for c, n in runs if c != 'grey']
    touching = any(runs[i][0] != 'grey' and runs[i + 1][0] != 'grey' for i in range(len(runs) - 1))
    ok = sorted(blocks) == [('blue', 2), ('green', 2), ('orange', 3), ('purple', 3)] and not touching
    return {'canon': 'valid gap packing' if ok else 'invalid packing', 'verdict': 'seat fills in row order: %s' % ' '.join(fills)}

# end of packing_code

# code: allfour_code
def orders_seated(confirms, fill_reads):
    """Which of the four order colours appear among the confirmed seats."""
    pairs = zip((fill_reads or {}).get('answers') or [], (confirms or {}).get('answers') or [])
    fills = [str(t).strip().lower().rstrip('.') for t, y in pairs if str(y).strip().lower().startswith('y')]
    have = sorted({v for v in fills if v in ('blue', 'orange', 'green', 'purple')})
    canon = 'all four orders seated' if len(have) == 4 else ('%d of four orders seated' % len(have))
    return {'canon': canon, 'verdict': 'order fills present on the row: %s' % (', '.join(have) or 'no order fill certified')}

# end of allfour_code
