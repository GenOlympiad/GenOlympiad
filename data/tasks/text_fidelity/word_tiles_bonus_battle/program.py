# code: law_code
def check_winner_margin(winner_read, margin_read, want_word, want_margin):
    """1.0 if the winning word and its points margin match the reference."""
    import re
    m = re.search(r'[A-Za-z]+', str(winner_read))
    if not m:
        return 0.0
    if m.group(0).upper() != str(want_word).upper():
        return 0.0
    try:
        margin = float(margin_read)
    except Exception:
        return 0.0
    if abs(margin - float(want_margin)) > 0.5:
        return 0.0
    return 1.0

# end of law_code
