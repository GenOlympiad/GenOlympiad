# code: helpers
from genolympiad.task_helpers import check_shadow_directions, count_confirmed_cutouts
# end of helpers

# code: m_code
def shadow_count_matches(count,t):
 """Score 1 if the number of shadows read equals the reference count."""
 try: value=float(count); want=float(t)
 except: return 0.0
 return 1.0 if abs(value-want)<0.5 else 0.0

# end of m_code
