# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: j_code
def j(t1,t2,t3,g1,g2,g3):
    def n(a): return str(a).strip().lower()[:5].rstrip() if isinstance(a,str) else ''
    def m(a):
        s=str(a).strip().lower()
        if s.startswith('left'): return 'left'
        if s.startswith('right'): return 'right'
        if s.startswith('level'): return 'level'
        return s
    return 1.0 if (m(t1)==g1 and m(t2)==g2 and m(t3)==g3) else 0.0

# end of j_code

# code: frac_code
def frac(t1,t2,t3,g1,g2,g3):
    def m(a):
        s=str(a).strip().lower()
        if s.startswith('left'): return 'left'
        if s.startswith('right'): return 'right'
        if s.startswith('level'): return 'level'
        return s
    got=[m(t1),m(t2),m(t3)]; want=[g1,g2,g3]
    return sum(1 for a,b in zip(got,want) if a==b)/3.0

# end of frac_code
