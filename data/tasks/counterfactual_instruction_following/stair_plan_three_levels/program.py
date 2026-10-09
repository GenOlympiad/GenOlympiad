# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_listed_items
# end of helpers

# code: plans_agree_code
def plans_agree(keys, arrows, breaks, want_a, want_b):
    """Count the plans whose arrows and break line read as specified; yes if all do."""
    want_arrows = dict(p.split('=') for p in str(want_a).split(',') if p.count('=') == 1)
    want_breaks = dict(p.split('=') for p in str(want_b).split(',') if p.count('=') == 1)
    panel_keys = [str(a).strip().upper() for a in ((keys or {}).get('answers') or [])]
    arrow_reads = [str(a).strip().lower() for a in ((arrows or {}).get('answers') or [])]
    break_reads = [str(a).strip().lower() for a in ((breaks or {}).get('answers') or [])]
    row = dict((k, (a, b)) for k, a, b in zip(panel_keys, arrow_reads, break_reads))
    n = sum(1 for k in want_arrows if row.get(k, ('', '')) == (want_arrows[k].strip().lower(), want_breaks.get(k, '').strip().lower()))
    return {'ok': 'yes' if want_arrows and n == len(want_arrows) else 'no', 'n': n,
            'verdict': '%d of the %d plans carry the flights and the break line the cut plane leaves in them' % (n, len(want_arrows))}

# end of plans_agree_code

# code: break_step_code
def break_step(keys, counts, panels, want):
    """Largest tread gap between a break line and the tread the cut plane falls on."""
    wanted_panels = [w.strip().upper() for w in str(panels).split(',') if w.strip()]
    panel_keys = [str(a).strip().upper() for a in ((keys or {}).get('answers') or [])]
    tread_counts = [str(a).strip() for a in ((counts or {}).get('answers') or [])]
    row = dict(zip(panel_keys, tread_counts))
    want_digits = ''.join(c for c in str(want) if c.isdigit())
    worst_gap = 0
    for w in wanted_panels:
        d = ''.join(c for c in str(row.get(w, '')) if c.isdigit())
        worst_gap = max(worst_gap, abs(int(d or 0) - int(want_digits or 0)))
    return {'gap': worst_gap, 'verdict': 'the worst of the %d break lines stands %d treads away from the tread the cut plane falls on' % (len(wanted_panels), worst_gap)}

# end of break_step_code
