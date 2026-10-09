# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_pivot_package
def band_flows(cells, nozz):
    import re
    nozz = dict(nozz or {})
    ans = cells.get('answers') if isinstance(cells, dict) else None
    ans = list(ans) if isinstance(ans, (list, tuple)) else []
    ys = {}
    for a in ans:
        m = re.search(r'b\s*(\d+)\D+n\s*(\d+)', str(a).lower())
        q = nozz.get(str(int(m.group(2)))) if m else None
        if q is not None:
            ys[int(m.group(1))] = float(q)
    return [ys[k] for k in sorted(ys)]

def flow_ramp(cells, nozzle_flows, ratio_max):
    """Check that per outlet flows rise band by band with evenly sized steps."""
    seq = band_flows(cells, nozzle_flows)
    steps = [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]
    ok = len(seq) >= 10 and bool(steps) and min(steps) > 0 and max(steps) <= float(ratio_max) * min(steps)
    return {'seq': seq, 'n': len(seq), 'steps': steps, 'verdict': 'ramp' if ok else 'flat',
            'note': '%d bands read off the pipe, per-outlet flows %s' % (len(seq), seq)}

def flow_total_matches(cells, nozzle_flows, duty, per_band, tol):
    """Check that the summed band flows match the total printed in the title block."""
    import re
    seq = band_flows(cells, nozzle_flows)
    answers = duty.get('answers') if isinstance(duty, dict) else None
    answers = list(answers) if isinstance(answers, (list, tuple)) else []
    m = re.search(r'\d+(?:\.\d+)?', str(answers[0] if answers else '').replace(',', ''))
    printed = float(m.group()) if m else -1.0
    total = float(per_band) * sum(seq)
    ok = len(seq) >= 10 and printed > 0 and abs(total - printed) <= float(tol) * printed
    return {'total': total, 'printed': printed,
            'verdict': 'balanced' if ok else 'unbalanced',
            'note': 'the twelve bands add to %.1f m3/h against the %.1f printed in the title block' % (total, printed)}

# end of code_pivot_package
