# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_key_match_count
def count_correct_leans(keys, vals, cols, want):
    """Count the columns whose read lean matches the specification: plumb or toward the middle."""
    wanted = dict(p.split('=') for p in str(want).split('|') if p.count('=') == 1)
    column_keys = [str(a).strip().upper().replace(' ', '')
          for a in ((keys or {}).get('answers') or [])]
    lean_reads = [str(a).strip().lower().replace('-', ' ')
          for a in ((vals or {}).get('answers') or [])]
    def geo(n):
        g = (n or {}).get('geometry') if isinstance(n, dict) else None
        return [b for b in (g or []) if isinstance(b, (list, tuple)) and len(b) >= 4]
    column_boxes = geo(cols)
    column_centres = {}
    for i, k in enumerate(column_keys):
        if k and i < len(column_boxes):
            column_centres[k] = (float(column_boxes[i][0]) + float(column_boxes[i][2])) / 2.0
    mid = column_centres.get('C3')
    if mid is None and column_centres:
        v = sorted(column_centres.values())
        mid = v[len(v) // 2]
    n, notes = 0, []
    for k, s in zip(column_keys, lean_reads):
        t = str(wanted.get(k, '')).strip().lower()
        if not t or not s:
            notes.append('column %s could not be read' % (k or '?'))
            continue
        if 'plumb' in t:
            if 'plumb' in s:
                n += 1
            notes.append('column %s should stand plumb and reads %r' % (k, s))
        elif mid is None or k not in column_centres:
            notes.append('column %s: the middle of the front could not be placed' % k)
        else:
            side = 'right' if column_centres[k] < mid else 'left'
            if side in s and 'plumb' not in s:
                n += 1
            notes.append('column %s: the middle lies to its %s on the page and it reads %r'
                       % (k, side, s))
    return {'n': n, 'asked': len(lean_reads), 'verdict': '; '.join(notes) or 'nothing was read'}

# end of code_key_match_count

# shared code: code_rank_run
def crack_scale_ranks(keys, vals, want, scale):
    """The scale rank of each ringed item, in the pinned run order, or empty if any is unread."""
    scale_words = [x.strip().lower() for x in str(scale).split('|')]
    run_order = [x.strip().upper() for x in str(want).split('|')]
    item_keys = [str(a).strip().upper().replace(' ', '') for a in ((keys or {}).get('answers') or [])]
    item_reads = [str(a).strip().lower() for a in ((vals or {}).get('answers') or [])]
    read_by_key = dict(zip(item_keys, item_reads))
    ranks = []
    for k in run_order:
        s = read_by_key.get(k, '')
        ranks.append(next((float(i) for i, w in enumerate(scale_words) if w and w in s), None))
    return {'seq': ranks if (ranks and all(x is not None for x in ranks)) else [], 'verdict': 'the ringed items read %s along the pinned run' % ranks}

# end of code_rank_run
