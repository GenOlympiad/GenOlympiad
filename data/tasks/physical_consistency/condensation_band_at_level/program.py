# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_misting_split
def first_answer(node):
    ans = (node or {}).get('answers') or []
    return str(ans[0] if ans else '').strip().lower()

def misting_split(iced, plain):
    """Split when the iced tumbler reads part misted and the room-temperature one none."""
    iced_read, plain_read = first_answer(iced), first_answer(plain)
    ok = iced_read.startswith('part') and plain_read.startswith('none')
    return {'iced': iced_read, 'plain': plain_read, 'verdict': 'split' if ok else 'nosplit',
            'note': 'the iced tumbler reads %s and the room-temperature tumbler reads %s'
                    % (iced_read, plain_read)}

# end of code_misting_split
