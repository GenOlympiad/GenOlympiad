# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: side_code
def pointer_side(stop_answer, n):
    """Say whether the read stop lies clockwise or counterclockwise of stop 1."""
    import re
    m = re.search(r'\d+', str(stop_answer or ''))
    if not m: return 'unread'
    k, n_stops = int(m.group(0)), int(n)
    return 'clockwise' if 1 < k <= 1 + n_stops // 2 else 'counterclockwise'

# end of side_code
