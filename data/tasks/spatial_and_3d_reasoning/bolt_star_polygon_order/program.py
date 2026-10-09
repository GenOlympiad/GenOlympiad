# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_star_walk
def classify_tightening_walk(letter_reads, number_reads):
    """Classify the chalked order over the eight studs as a star or a walk around the rim."""
    import re
    stud_at_pass = {}
    for t, v in zip((letter_reads or {}).get('answers') or [], (number_reads or {}).get('answers') or []):
        a, b = re.search(r'[A-H]', str(t).upper()), re.search(r'[1-8]', str(v))
        if a and b: stud_at_pass[int(b.group(0))] = 'ABCDEFGH'.index(a.group(0))
    if sorted(stud_at_pass) != [1, 2, 3, 4, 5, 6, 7, 8] or len(set(stud_at_pass.values())) != 8:
        return {'state': 'incomplete', 'verdict': 'the chalked numbers do not cover passes 1-8 over the eight lettered studs once each'}
    hops = [min((stud_at_pass[k + 1] - stud_at_pass[k]) % 8, (stud_at_pass[k] - stud_at_pass[k + 1]) % 8) for k in range(1, 8)]
    if min(hops) < 2: return {'state': 'ring', 'verdict': 'a pass steps to a neighbouring stud -- the walk runs the rim instead of crossing it'}
    if sum(1 for h in hops if h >= 3) < 4: return {'state': 'ring', 'verdict': 'too few passes cross the flange -- the walk hugs the rim'}
    return {'state': 'star', 'verdict': 'every pass jumps the rim and most cross the flange -- the chalk walk traces a star'}

# end of code_star_walk
