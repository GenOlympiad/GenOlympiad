# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_bottle_source
def check_bottle_regions(region_read, grape_read, shape_read, shape_of, grapes):
    """Count bottles whose shoulder shape and named grape fit the region on their label."""
    def ans(n):
        return ((n or {}).get('answers') or [])
    def look(tbl, r):
        return ([v for k, v in tbl if k in r] or ['~'])[0]
    region_answers, grape_answers, shape_answers = ans(region_read), ans(grape_read), ans(shape_read)
    rows, n_shape_ok, n_grape_ok = [], 0, 0
    for i, a in enumerate(region_answers):
        r = str(a).lower()
        owed_shape = look(shape_of, r)
        drawn = str(shape_answers[i]).lower() if i < len(shape_answers) else '(no read)'
        g = str(grape_answers[i]).lower() if i < len(grape_answers) else '(no read)'
        s_ok = owed_shape != '~' and owed_shape in drawn
        g_ok = any(x in g for x in look(grapes, r).split('|'))
        n_shape_ok += 1 if s_ok else 0
        n_grape_ok += 1 if g_ok else 0
        rows.append('bottle %d (label %s): shoulder owed %s, drawn %s -> %s; grape %s -> %s'
                    % (i + 1, str(a).upper(), owed_shape, drawn, 'shape OK' if s_ok else 'shape WRONG',
                       g, 'permitted' if g_ok else 'NOT PERMITTED'))
    return {'n_shape_ok': n_shape_ok, 'n_grape_ok': n_grape_ok, 'n': len(region_answers), 'rows': rows,
            'verdict': ' | '.join(rows) + ' || %d of %d bottles carry the shape their own region uses; %d name a grape that region may use' % (n_shape_ok, len(region_answers), n_grape_ok)}

# end of code_bottle_source
