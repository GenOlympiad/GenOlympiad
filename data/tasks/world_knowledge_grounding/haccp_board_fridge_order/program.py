# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_shelf_order
def shelf_order(letters, foods, want):
    """Score shelves against the risk order, 0.5 if one neighbouring pair is swapped."""
    shelf_letters = [''.join(c for c in str(a).upper() if c.isalpha())[:1] for a in (letters or {}).get('answers') or []]
    tray_foods = [''.join(c for c in str(b).lower() if c.isalpha()) for b in (foods or {}).get('answers') or []]
    rows = {}
    for k, v in zip(shelf_letters, tray_foods):
        if not k or not v or k in rows:
            return {'unreadable': True, 'frac': 0.0, 'canon': '',
                    'verdict': 'a tray came back with no shelf letter, no food, or a shelf letter already used -> honest refusal'}
        rows[k] = v
    keys = sorted(rows)
    got = [rows[k] for k in keys]
    reference_order = [p.split(':')[1] for p in str(want).split()]
    canon = ' '.join('%s:%s' % (k.lower(), rows[k]) for k in keys)
    if len(got) != len(reference_order) or sorted(got) != sorted(reference_order):
        return {'unreadable': False, 'frac': 0.0, 'canon': canon,
                'verdict': 'the shelves do not carry the five docket items one to a shelf: ' + canon}
    misplaced = [i for i in range(len(reference_order)) if got[i] != reference_order[i]]
    score = 1.0 if not misplaced else (0.5 if len(misplaced) == 2 and misplaced[1] - misplaced[0] == 1 else 0.0)
    return {'unreadable': False, 'frac': score, 'canon': canon,
            'verdict': 'the shelves read %s -> %s' % (canon, 'the risk order' if score == 1.0 else ('the risk order with one neighbouring pair swapped' if score == 0.5 else 'not the risk order'))}

# end of code_shelf_order

# shared code: code_frac_of
def frac_of(node):
    """The score stored on the given result, or 0 if it is missing."""
    try:
        return float((node or {}).get('frac') or 0.0)
    except Exception:
        return 0.0

# end of code_frac_of

# code: board_match_code
def board_match(foods, cols, want):
    """Share of foods lying on the board colour the trade code gives them."""
    board_foods = [''.join(c for c in str(a).lower() if c.isalpha()) for a in (foods or {}).get('answers') or []]
    board_colours = [''.join(c for c in str(b).lower() if c.isalpha()) for b in (cols or {}).get('answers') or []]
    rows = {}
    for k, v in zip(board_foods, board_colours):
        if not k or not v or k in rows:
            return {'unreadable': True, 'frac': 0.0, 'canon': '', 'verdict': 'a board came back with no food, no colour, or a food already seen on another board -> honest refusal'}
        rows[k] = v
    reference_map = dict(p.split(':') for p in str(want).split())
    matched = sum(1 for k in reference_map if rows.get(k) == reference_map[k])
    canon = ' '.join('%s:%s' % (k, rows[k]) for k in sorted(rows))
    return {'unreadable': False, 'frac': round(float(matched) / len(reference_map), 4), 'canon': canon, 'verdict': '%d of the %d foods lie on the colour the trade code gives them: %s' % (matched, len(reference_map), canon)}

# end of board_match_code

# code: stacking_code
def raw_below_cooked(letters, foods):
    """Yes if no raw tray stands on a shelf above the cooked gammon tray."""
    shelf_letters = [''.join(c for c in str(a).upper() if c.isalpha())[:1] for a in (letters or {}).get('answers') or []]
    tray_foods = [''.join(c for c in str(b).lower() if c.isalpha()) for b in (foods or {}).get('answers') or []]
    raw = ('salmon', 'beef', 'chicken')
    seen = [(k, v) for k, v in zip(shelf_letters, tray_foods) if k and v and v != 'none']
    if not any(v in raw for k, v in seen) or not any(v == 'gammon' for k, v in seen):
        return {'unreadable': True, 'ok': 'no', 'verdict': 'the trays did not give back both a raw item and the cooked one with their shelf letters -> honest refusal'}
    cooked = min(k for k, v in seen if v == 'gammon')
    bad = sorted(k for k, v in seen if v in raw and k < cooked)
    return {'unreadable': False, 'ok': 'no' if bad else 'yes', 'verdict': ('raw food stands on shelf %s, above the cooked tray on shelf %s' % (','.join(bad), cooked)) if bad else 'no raw tray stands above the cooked one'}

# end of stacking_code
