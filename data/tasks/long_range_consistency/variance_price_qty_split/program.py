# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: split_code
def read_variance_figures(name_read, figure_read):
    """Pair each variance step, as usage or price, with its read figure."""
    names = [str(x).lower() for x in (name_read or {}).get('answers') or []]
    figs = [''.join(c for c in str(x) if c.isdigit()) for x in (figure_read or {}).get('answers') or []]
    rows = {}
    for i, nm in enumerate(names):
        used = 'usage' in nm or 'quantity' in nm or 'volume' in nm or 'efficiency' in nm
        key = 'usage' if used else ('price' if ('price' in nm or 'rate' in nm) else 'other%d' % i)
        rows[key] = ((figs[i] if i < len(figs) else '').lstrip('0') or '0')
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'verdict': 'the floating steps read %s' % (seq or 'nothing')}

# end of split_code

# code: sides_code
def read_variance_sides(name_read, word_read):
    """Mark each usage or price variance step as adverse, favourable or unclear."""
    names = [str(x).lower() for x in (name_read or {}).get('answers') or []]
    words = [str(x).lower() for x in (word_read or {}).get('answers') or []]
    rows = {}
    for i, nm in enumerate(names):
        used = 'usage' in nm or 'quantity' in nm or 'volume' in nm or 'efficiency' in nm
        key = 'usage' if used else ('price' if ('price' in nm or 'rate' in nm) else 'other%d' % i)
        got = words[i] if i < len(words) else ''
        rows[key] = 'adverse' if 'adv' in got else ('favourable' if 'fav' in got else 'unclear')
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'verdict': 'the floating steps are marked %s' % (seq or 'nothing')}

# end of sides_code
