# code: m_code
def winner_named(answer, target):
    """1 if the reference winner's name appears in the read answer, else 0."""
    if answer is None: return {'frac':0.0,'unreadable':True}
    return {'frac': 1.0 if str(target).lower() in str(answer).lower() else 0.0, 'unreadable':False}

# end of m_code

# code: w_code
def score_fraction(result):
    """The score fraction from the winner check as a float."""
    return float(result['frac'])

# end of w_code
