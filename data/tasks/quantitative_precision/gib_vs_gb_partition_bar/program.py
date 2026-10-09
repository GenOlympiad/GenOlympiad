# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: lines_ok_code
def window_lines_match(node, reference):
    """Mark each window line (capacity, used, free) yes if within 1% of the reference GB."""
    import re
    want = {'capacity': float(reference.cap_gb), 'used': float(reference.used_gb), 'free': float(reference.free_gb)}
    seen, answers = {}, ((node or {}).get('answers') if isinstance(node, dict) else None)
    for a in (answers if isinstance(answers, (list, tuple)) else []):
        t = str(a).replace(',', '').lower()
        m = re.search(r'(\d+(?:\.\d+)?)\s*gb', t) or re.search(r'(\d+(?:\.\d+)?)', t)
        for k in want:
            if k in t and m:
                seen[k] = float(m.group(1))
    rows = [['yes' if k in seen and abs(seen[k] - want[k]) <= 0.01 * want[k] else 'no'] for k in ('capacity', 'used', 'free')]
    return {'rows': rows, 'n': len(seen), 'seen': 'window lines read: %s' % seen}

# end of lines_ok_code

# code: figures_differ_code
def figures_differ(carton_read, window_read, reference):
    """Yes if the window figure is below the carton figure and matches the converted GB."""
    import re
    def gb(node):
        ans = (node or {}).get('answers') if isinstance(node, dict) else None
        t = ' '.join(str(x) for x in (ans if isinstance(ans, (list, tuple)) else [])).replace(',', '').lower()
        m = re.search(r'(\d+(?:\.\d+)?)\s*(tb|gb)?', t)
        return None if not m else float(m.group(1)) * (1000.0 if m.group(2) == 'tb' else 1.0)
    carton_gb, window_gb = gb(carton_read), gb(window_read)
    reference_gb = float(reference.cap_gb)
    ok = carton_gb is not None and window_gb is not None and window_gb < 0.97 * carton_gb and abs(window_gb - reference_gb) <= 0.01 * reference_gb
    return {'ok': 'yes' if ok else 'no',
            'seen': 'carton %s GB, window %s GB, converted truth %s GB' % (carton_gb, window_gb, reference_gb)}

# end of figures_differ_code
