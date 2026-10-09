# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, map_answer_to_token
# end of helpers

# code: track_err_code
def worst_wheeling_error(keys, marks, want):
    """The largest gap between a pressed wheeling found and the gap the drill setting wants."""
    wanted = sorted(float(x) for x in str(want).split(',') if x.strip().isdigit())
    gap_numbers = [''.join(c for c in str(a) if c.isdigit()) for a in ((keys or {}).get('answers') or [])]
    marks_read = [str(a).strip().lower() for a in ((marks or {}).get('answers') or [])]
    pressed = sorted(float(k) for k, v in zip(gap_numbers, marks_read) if k and v.startswith('y'))
    if len(pressed) != len(wanted):
        return {'err': 99.0, 'found': len(pressed),
                'verdict': '%d wheelings were found where %d were wanted' % (len(pressed), len(wanted))}
    worst = max([abs(a - b) for a, b in zip(pressed, wanted)] or [99.0])
    return {'err': worst, 'found': len(pressed),
            'verdict': 'the worst wheeling is %.0f gaps away from the gap the drill setting puts it in' % worst}

# end of track_err_code

# code: crushed_code
def count_crushed_rows(keys, over, rows):
    """Count rows read as carrying a wheel track, or 99 if not every row was read."""
    row_numbers = [''.join(c for c in str(a) if c.isdigit()) for a in ((keys or {}).get('answers') or [])]
    marks_read = [str(a).strip().lower() for a in ((over or {}).get('answers') or [])]
    seen = len([k for k in row_numbers if k])
    bad = len([1 for k, v in zip(row_numbers, marks_read) if k and v.startswith('y')])
    r = ''.join(c for c in str(rows) if c.isdigit())
    n = bad if (r and seen == int(r)) else 99
    return {'n': n, 'seen': seen,
            'verdict': '%d of the %d rows that were read carry a wheel track along them' % (bad, seen)}

# end of crushed_code
