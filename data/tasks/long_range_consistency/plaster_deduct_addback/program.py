# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: codes_code
def opening_codes(node):
    """The distinct opening codes read, upper cased and sorted, joined by bars."""
    raw = [str(x).strip().upper() for x in (node or {}).get('answers') or []]
    seen = sorted(set(c.replace(' ', '') for c in raw if c))
    return {'seq': '|'.join(seen), 'n': len(seen),
            'verdict': 'tinted openings read back as %s' % ('|'.join(seen) or 'none')}

# end of codes_code

# code: netfig_code
def net_area_text(node):
    """The net plaster area read, as text with two decimals when it is a number."""
    raw = str(((node or {}).get('answers') or [''])[0])
    keep = ''.join(c for c in raw if c.isdigit() or c == '.')
    try:
        txt = '%.2f' % float(keep)
    except ValueError:
        txt = keep or 'unreadable'
    return {'txt': txt, 'verdict': 'net plaster area reads %s' % txt}

# end of netfig_code
