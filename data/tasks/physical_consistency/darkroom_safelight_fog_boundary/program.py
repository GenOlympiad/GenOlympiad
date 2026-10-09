# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_fog_split
def first_answer(node):
    ans = node.get('answers') if isinstance(node, dict) else None
    ans = list(ans) if isinstance(ans, (list, tuple)) else []
    return str(ans[0] if ans else '').strip().lower()

def fog_split_check(test, edge, ctrl, want_test, want_edge, want_ctrl):
    """Split when the exposed sheet, its boundary and the boxed sheet all read as expected."""
    test_read, edge_read, control_read = first_answer(test), first_answer(edge), first_answer(ctrl)
    ok = (test_read.startswith(str(want_test).strip().lower())
          and edge_read.startswith(str(want_edge).strip().lower())
          and control_read.startswith(str(want_ctrl).strip().lower()))
    return {'test': test_read, 'edge': edge_read, 'control': control_read, 'verdict': 'split' if ok else 'nosplit',
            'note': 'the sheet that lay out reads %s with a %s boundary and the sheet that stayed in the box reads %s' % (test_read, edge_read or 'unread', control_read)}

# end of code_fog_split
