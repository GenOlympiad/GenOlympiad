# code: helpers
from genolympiad.task_helpers import all_items_satisfy, any_item_satisfies
# end of helpers

# shared code: code_3f245bf0309d
def read_yes_no(answers):
    """1 if the first answer says yes, 0 if it says no, marked unread otherwise."""
    a = answers or []
    s = str(a[0]).strip().lower() if a and a[0] is not None else ''
    words = ''.join((c if c.isalnum() else ' ') for c in s).split()
    reply = None
    for w in words:
        if w in ('yes', 'no'):
            reply = w
            break
    if reply is None:
        return {'frac': 0.0, 'answer': s[:60], 'unread': True}
    return {'frac': (1.0 if reply == 'yes' else 0.0), 'answer': reply, 'unread': False}

# end of code_3f245bf0309d
