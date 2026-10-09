# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_power_reads
def power_reads(ids, node, unshaded, shaded):
    """Ratio of the shaded module's watts to the unshaded one, paired by module number."""
    import re
    def num(x):
        m = re.search(r'-?\d+(?:\.\d+)?', str(x).replace(',', ''))
        return float(m.group()) if m else None
    def key(x):
        m = re.search(r'\d+', str(x))
        return m.group().lstrip('0') if m else None
    watts = [num(a) for a in ((node or {}).get('answers') or [])]
    module_keys = [key(a) for a in ((ids or {}).get('answers') or [])]
    watts_by_module = {k: watts[i] for i, k in enumerate(module_keys) if k and i < len(watts)}
    left, right = watts_by_module.get(key(unshaded)), watts_by_module.get(key(shaded))
    how = 'paired by the stencilled module number'
    if left is None or right is None:
        (left, right), how = (watts + [None, None])[:2], 'positional fallback: the stencilled numbers did not both read'
    ratio = right / left if (left is not None and right is not None and left > 1.0) else 9.0
    return {'left': left, 'right': right, 'ratio': ratio, 'how': how,
            'verdict': 'unshaded %s reads %s W, shaded %s reads %s W -> shaded/unshaded = %s (%s)' % (unshaded, left, shaded, right, ratio, how)}

# end of code_power_reads
