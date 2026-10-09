# code: cut_letter_code
def cut_letter(bank_a):
    """The bank letter named for the cut bank: A for the cliff, B for the beach."""
    s = str(bank_a or '').strip().lower()
    if 'cliff' in s:
        return 'A'
    if 'beach' in s:
        return 'B'
    return None

# end of cut_letter_code

# code: bar_letter_code
def bar_letter(bank_b):
    """The bank letter named for the point bar: B for the beach, A for the cliff."""
    s = str(bank_b or '').strip().lower()
    if 'beach' in s:
        return 'B'
    if 'cliff' in s:
        return 'A'
    return None

# end of bar_letter_code
