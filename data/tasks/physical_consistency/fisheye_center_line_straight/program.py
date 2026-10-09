# code: helpers
from genolympiad.task_helpers import map_answer_to_token
# end of helpers

# code: both_edges_bow_code
def both_edges_bow(top, bottom):
    """Answer yes only when both the top and the bottom edge stripes read as bowed."""
    def sits_on_the_straight_join(r):
        a = (r.get('answers') or [None])[0] if isinstance(r, dict) else r
        s = str(a or '').strip().lower()
        if s.startswith('yes'):
            return True
        if s.startswith('no'):
            return False
        return None
    vals = [sits_on_the_straight_join(top), sits_on_the_straight_join(bottom)]
    return 'yes' if all(v is False for v in vals) else 'no'

# end of both_edges_bow_code
