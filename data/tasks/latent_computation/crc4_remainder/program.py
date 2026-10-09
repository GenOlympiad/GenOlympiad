# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: seq_exact_code
def seq_exact(read, target):
    """Score 1 when the read digits begin with exactly the target remainder bits."""
    import re
    if read is None:
        return 0.0
    if isinstance(read, str):
        tokens = re.findall(r'-?\d+', read)
    elif isinstance(read, (list, tuple)):
        tokens = []
        for t in read:
            m = re.findall(r'-?\d+', str(t))
            tokens.append(m[0] if m else str(t))
    else:
        tokens = [str(read)]
    if len(tokens) < len(target):
        return 0.0
    for i in range(len(target)):
        try:
            if int(tokens[i]) != int(target[i]):
                return 0.0
        except (TypeError, ValueError):
            return 0.0
    return 1.0

# end of seq_exact_code
