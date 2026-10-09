# code: law_code
def column_and_row_spell_words(down, across, want_down, want_across):
    """1 if the left column and the top row spell the two required words, else 0."""
    import re
    SUB = {'0':'O','1':'I','5':'S','8':'B','2':'Z'}
    def norm(s):
        s = ''.join(SUB.get(ch, ch) for ch in str(s).upper())
        return re.sub(r'[^A-Z]', '', s)
    if norm(down) != norm(want_down):
        return 0.0
    if norm(across) != norm(want_across):
        return 0.0
    return 1.0

# end of law_code
