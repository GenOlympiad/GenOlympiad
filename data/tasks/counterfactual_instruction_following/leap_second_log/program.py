# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_listed_items
# end of helpers

# code: interlock_code
def rows_and_step_match(rows, step, want_rows, want_step):
    """Whether every expected time row is listed and the level change sits at the expected stamp."""
    wanted_rows = set(w.strip() for w in str(want_rows).split(',') if w.strip())
    rows_read = set(str(a).strip() for a in ((rows or {}).get('answers') or []))
    step_at = str((((step or {}).get('answers') or ['none'])[0])).strip()
    ok = 'yes' if wanted_rows and wanted_rows.issubset(rows_read) and step_at == str(want_step).strip() else 'no'
    return {'ok': ok, 'missing': sorted(wanted_rows - rows_read), 'step_at': step_at,
            'verdict': 'the table is missing %s and the level change stands over %s'
                       % ('/'.join(sorted(wanted_rows - rows_read)) or 'nothing', step_at or 'nothing')}

# end of interlock_code

# code: drop_rows_code
def largest_row_drop(node):
    """The largest number of grid rows the stepped line drops where it changes level."""
    answers = [str(a).strip() for a in ((node or {}).get('answers') or [])]
    n = 0
    for a in answers:
        d = ''.join(c for c in a if c.isdigit())
        n = max(n, int(d)) if d else n
    return {'n': n, 'asked': len(answers),
            'verdict': 'the stepped line drops %d grid rows where it changes level' % n}

# end of drop_rows_code
