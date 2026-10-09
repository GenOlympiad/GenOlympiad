# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: j_code
def j(a1,a2,a3,rn,g1,g2,g3,gr):
    def yn(a): return str(a).strip().lower().startswith('yes') if isinstance(a,str) else False
    ok1 = yn(a1)==(g1=='yes')
    ok2 = yn(a2)==(g2=='yes')
    ok3 = yn(a3)==(g3=='yes')
    try: okr = abs(float(rn)-float(gr))<0.5
    except Exception: return 0.0
    return 1.0 if (ok1 and ok2 and ok3 and okr) else 0.0

# end of j_code
