# code: qs_code
def tick_questions(reference):
    """List the level question for each queried tick of the output trace."""
    tick_questions=reference['q_ticks']; query_ticks=reference['query_ticks']
    return [tick_questions[str(t)] for t in query_ticks]

# end of qs_code

# code: score_code
def lvl(x):
    s=str(x).strip().upper()
    if 'HIGH' in s or s in ('1','H','UP','TOP'): return 1
    if 'LOW' in s or s in ('0','L','DOWN','BOTTOM'): return 0
    return -1
def score(a0,a1,a2,gt):
    tg=gt['targets']; got=[a0,a1,a2]
    ok=all(lvl(got[i])==int(tg[i]) for i in range(3))
    return 1.0 if ok else 0.0

# end of score_code

# code: m_code
def level_matches(answer, target):
    """1 if the expected level word appears in the answer, else 0."""
    if answer is None: return 0.0
    return 1.0 if str(target).upper() in str(answer).upper() else 0.0

# end of m_code
