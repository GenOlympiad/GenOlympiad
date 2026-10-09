# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: excess_tok_code
def excess_token(declared_read, actual_read):
    """A token for how much the actual fill exceeds the declared volume, such as plus0.5."""
    import re
    a = str((((declared_read or {}).get('answers') or []) + [''])[0])
    b = str((((actual_read or {}).get('answers') or []) + [''])[0])
    x = re.search(r'\d+(?:\.\d+)?', a)
    y = re.search(r'\d+(?:\.\d+)?', b)
    declared = float(x.group()) if x else None
    actual = float(y.group()) if y else None
    tok = 'plus%g' % round(actual - declared, 3) if (declared is not None and actual is not None) else 'none'
    return {'tok': tok, 'n': 2,
            'verdict': 'record books %s declared against %s actual' % (declared, actual)}

# end of excess_tok_code
