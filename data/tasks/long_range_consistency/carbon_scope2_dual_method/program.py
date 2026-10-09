# code: paired_code
def read_column_figures(name_reads, figure_reads):
    """Pair each column's method name, market or location, with its printed figure."""
    names = [str(x).lower() for x in (name_reads or {}).get('answers') or []]
    figures = [''.join(c for c in str(x) if c.isdigit()) for x in (figure_reads or {}).get('answers') or []]
    rows = {}
    for i, name in enumerate(names):
        key = 'market' if 'market' in name else ('location' if ('location' in name or 'grid' in name) else 'other%d' % i)
        rows[key] = ((figures[i] if i < len(figures) else '').lstrip('0') or '0')
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'verdict': 'the two columns read %s' % (seq or 'nothing')}

# end of paired_code

# code: onefig_code
def read_cap_figure(node):
    """Keep the digits of the figure printed on the cap label."""
    raw = str((((node or {}).get('answers') or [''])[0]) or '')
    digits = ''.join(c for c in raw if c.isdigit()).lstrip('0') or 'none'
    return {'txt': digits, 'verdict': 'the cap is labelled %s tonnes' % digits}

# end of onefig_code
