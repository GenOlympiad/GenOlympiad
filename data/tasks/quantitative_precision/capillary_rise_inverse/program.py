# code: invariant_code
def rise_width_product_score(rise_boxes, width_boxes, reference):
    """Score how constant rise times width stays across the tubes, 0 if all rises are equal."""
    def cx(b):
        return (float(b[1]) + float(b[3])) / 2.0
    rise_marks = sorted(((cx(b), abs(float(b[2]) - float(b[0]))) for b in (rise_boxes.get('geometry') or [])))
    width_marks = sorted(((cx(b), abs(float(b[3]) - float(b[1]))) for b in (width_boxes.get('geometry') or [])))
    n = min(len(rise_marks), len(width_marks))
    min_items = int(reference['min_items'])
    if n < min_items:
        return {'frac': 0.0, 'degenerate': True, 'n_items': n,
                'caption': 'degenerate read (%d paired rise/width marks, need %d)' % (n, min_items)}
    rises = [rise_marks[i][1] for i in range(n)]
    products = [rise_marks[i][1] * width_marks[i][1] for i in range(n)]
    mean_h = sum(rises) / float(n)
    if mean_h <= 0 or min(products) <= 0:
        return {'frac': 0.0, 'degenerate': True, 'n_items': n,
                'caption': 'degenerate read (a rise or width mark measured zero)'}
    spread = (max(rises) - min(rises)) / mean_h
    if spread < float(reference['size_min']):
        return {'frac': 0.0, 'degenerate': False, 'n_items': n, 'spread': round(spread, 4),
                'prod_cv': None,
                'caption': 'all tubes drawn at the same rise (spread %.3f < %.2f): the equal-rise '
                           'default, not an inverse law' % (spread, float(reference['size_min']))}
    mean_p = sum(products) / float(n)
    var = sum((p - mean_p) ** 2 for p in products) / float(n)
    cv = (var ** 0.5) / mean_p
    tol = float(reference['tol'])
    score = max(0.0, 1.0 - cv / (2.0 * tol))
    return {'frac': round(score, 4), 'degenerate': False, 'n_items': n, 'spread': round(spread, 4),
            'prod_cv': round(cv, 4), 'products': [round(p, 1) for p in products],
            'caption': 'rise x width across %d tubes varies by CV %.3f (0 = a perfect inverse '
                       'law; tol %.2f)' % (n, cv, tol)}

# end of invariant_code
