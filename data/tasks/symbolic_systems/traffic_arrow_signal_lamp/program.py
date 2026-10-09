# code: score_code
import re
def lit(x):
    s = str(x if x is not None else '').lower()
    if re.search(r'\b(bright|lit|glowing|on)\b', s): return True
    if re.search(r'\b(dark|unlit|off|dull|black)\b', s): return False
    return None
def mark(x):
    s = str(x if x is not None else '').lower()
    if re.search(r'\bleft\b', s): return 'arrow-left'
    if re.search(r'\bright\b', s): return 'arrow-right'
    if re.search(r'\b(up|upward|upwards|straight|ahead)\b', s): return 'arrow-straight'
    if re.search(r'\b(disc|disk|circle|blob|round|solid|filled)\b', s): return 'disc'
    if re.search(r'\b(none|nothing|empty)\b', s): return 'none'
    return None
def score_lit_lens(lt, lm, lb, mt, mm, mb, reference):
    """1 if exactly one lens is lit and its place and marking match the reference, else 0."""
    states = [lit(lt), lit(lm), lit(lb)]
    if any(s is None for s in states): return 0.0
    lit_lenses = [i for i, s in enumerate(states) if s]
    if len(lit_lenses) != 1: return 0.0
    i = lit_lenses[0]
    position = ['top', 'middle', 'bottom'][i]
    shape = mark([mt, mm, mb][i])
    if shape is None: return 0.0
    return 1.0 if (position == reference['lit_position'] and shape == reference['shape_answer']) else 0.0

# end of score_code
