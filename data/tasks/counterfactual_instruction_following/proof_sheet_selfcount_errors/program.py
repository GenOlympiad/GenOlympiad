# shared code: code_line_diff
def _norm(s):
    t = ' '.join(str(s or '').lower().split())
    return ''.join(c for c in t if c.isalnum() or c in ' .-')


def count_lines_as_specified(keys, vals, want):
    """Count the numbered lines whose text matches the house copy exactly."""
    expected = [_norm(x) for x in str(want or '').split('|')]
    line_numbers = [''.join(c for c in str(k or '') if c.isdigit())
          for k in (keys or {}).get('answers') or []]
    line_texts = [_norm(v) for v in (vals or {}).get('answers') or []]
    rows = {}
    for i, k in enumerate(line_numbers):
        if k and k not in rows:
            rows[k] = line_texts[i] if i < len(line_texts) else ''
    if not rows:
        return {'n_ok': 0, 'refused': True,
                'verdict': 'no line cut-out came back with a line number -> abstain'}
    ok, bad = 0, []
    for k, got in rows.items():
        try:
            idx = int(k) - 1
        except ValueError:
            bad.append('line %s unreadable' % k)
            continue
        if 0 <= idx < len(expected) and got == expected[idx]:
            ok += 1
        else:
            bad.append('line %s reads "%s"' % (k, got))
    return {'n_ok': ok, 'asked': len(rows),
            'verdict': '%d of %d lines stand as specified%s'
                       % (ok, len(rows), ('; ' + '; '.join(bad)) if bad else '')}

# end of code_line_diff

# code: stamped_code
def stamped_fault_count(node):
    """The most common figure read from the stamp, the declared fault count."""
    numbers = [''.join(c for c in str(a or '') if c.isdigit())
          for a in (node or {}).get('answers') or []]
    numbers = [n for n in numbers if n]
    if not numbers:
        return {'num': 'none', 'refused': True,
                'verdict': 'the cut-out of the stamp came back with no figure -> abstain'}
    top = max(set(numbers), key=numbers.count)
    return {'num': top, 'verdict': 'the stamp declares %s faults' % top}

# end of stamped_code
