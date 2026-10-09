# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: joint_code
def joint(nA,nB,nC,nD,nE,nF,nG, gA,gB,gC,gD,gE,gF,gG):
    got=[nA,nB,nC,nD,nE,nF,nG]; want=[gA,gB,gC,gD,gE,gF,gG]
    for x in got:
        try: float(x)
        except Exception: return 0.0
    return 1.0 if all(abs(float(a)-float(b))<0.5 for a,b in zip(got,want)) else 0.0

# end of joint_code

# code: frac_code
def frac(pA,pB,pC,pD,pE,pF,pG, gA,gB,gC,gD,gE,gF,gG):
    got=[pA,pB,pC,pD,pE,pF,pG]; want=[gA,gB,gC,gD,gE,gF,gG]; ok=0
    for a,b in zip(got,want):
        try:
            if abs(float(a)-float(b))<0.5: ok+=1
        except Exception: pass
    return ok/7.0

# end of frac_code
