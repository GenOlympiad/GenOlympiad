# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: issues_code
def issue_figures_in_order(stage_names, issue_reads, order):
    """The ISSUE figure read for each stage, listed in work-flow order."""
    import re
    names = [str(x).strip().lower() for x in (stage_names or {}).get('answers') or []]
    figure_matches = [re.search(r'\d+', str(x).replace(',', '')) for x in (issue_reads or {}).get('answers') or []]
    figure_by_stage = {}
    for i, t in enumerate(names):
        if t and i < len(figure_matches) and figure_matches[i]:
            figure_by_stage.setdefault(t, figure_matches[i].group())
    row = [figure_by_stage.get(s, '') for s in order]
    return {'grid': [row], 'n': sum(1 for c in row if c),
            'verdict': 'ISSUE figures read in flow order: %s' % ', '.join(c or '-' for c in row)}

# end of issues_code

# code: upstream_code
def count_upstream_arrows(arrow_reads):
    """Count the panels whose dashed arrowhead is read as pointing left, upstream."""
    answers = [str(x).strip().lower() for x in (arrow_reads or {}).get('answers') or []]
    n = sum(1 for t in answers if t.startswith('left'))
    return {'n': n, 'asked': len(answers),
            'verdict': '%d of the %d panels carry a dashed arrowhead pointing upstream'
                       % (n, len(answers))}

# end of upstream_code

# code: falls_code
def issues_fall_along_flow(stage_names, issue_reads, order):
    """Yes when every stage has an ISSUE figure and each is larger than the next."""
    import re
    names = [str(x).strip().lower() for x in (stage_names or {}).get('answers') or []]
    figure_matches = [re.search(r'\d+', str(x).replace(',', '')) for x in (issue_reads or {}).get('answers') or []]
    figure_by_stage = {}
    for i, t in enumerate(names):
        if t and i < len(figure_matches) and figure_matches[i]:
            figure_by_stage.setdefault(t, int(figure_matches[i].group()))
    figures = [figure_by_stage[s] for s in order if s in figure_by_stage]
    ok = len(figures) == len(order) and all(x > y for x, y in zip(figures, figures[1:]))
    return {'falls': 'yes' if ok else 'no', 'seq': figures,
            'verdict': 'issue quantities along the flow: %s' % figures}

# end of falls_code
