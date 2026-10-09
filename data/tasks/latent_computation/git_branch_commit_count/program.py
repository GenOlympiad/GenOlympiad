# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: j_code
def j(cm,cf,gm,gf):
    try:
        okm = abs(float(cm)-float(gm))<0.5
        okf = abs(float(cf)-float(gf))<0.5
    except Exception: return 0.0
    return 1.0 if (okm and okf) else 0.0

# end of j_code
