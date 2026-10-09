# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_round_amp
def neutral_whole_amps(node):
    """The neutral clamp reading, to the nearest whole amp."""
    import re
    answers = (node or {}).get('answers') or ['']
    m = re.search(r'\d+(?:\.\d+)?', str(answers[0]).replace(',', ''))
    amp = str(int(round(float(m.group(0))))) if m else '?'
    return {'amp': amp, 'verdict': 'the neutral clamp reads %s A after rounding to whole amps' % amp}

# end of code_round_amp

# shared code: code_phase_pairs
def phase_pairs(letter_reads, value_reads):
    """Each phase letter paired with its clamp reading in whole amps, sorted."""
    import re
    letters = [re.sub(r'[^a-z]', '', str(x).lower())[:1] for x in (letter_reads or {}).get('answers') or []]
    figs = []
    for x in (value_reads or {}).get('answers') or []:
        m = re.search(r'\d+(?:\.\d+)?', str(x).replace(',', ''))
        figs.append(str(int(round(float(m.group(0))))) if m else '?')
    rows = sorted('%s:%s' % (l, f) for l, f in zip(letters, figs) if l)
    return {'pairs': '|'.join(rows), 'verdict': 'the phase clamps read %s' % ', '.join(rows)}

# end of code_phase_pairs
