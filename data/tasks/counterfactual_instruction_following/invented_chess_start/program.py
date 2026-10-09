# code: kchk_code
def file_matches_reference(answer, want):
    """Score 1 if the file letter named in the answer is the expected file."""
    if answer is None or isinstance(answer, dict): return 0.0
    import re
    t = str(answer).strip().lower()
    m = re.search(r'(?:file|column|col)\s*([a-h])\b', t)
    if not m:
        m = re.search(r'\b([a-h])\s*(?:file|column|-file)\b', t)
    if not m:
        m = re.search(r'\b([a-h])[1-8]\b', t)
    if not m:
        letters = re.findall(r'\b([a-h])\b', t)
        if len(letters) == 1: m = re.match(r'([a-h])', letters[0])
    if not m: return 0.0
    return 1.0 if m.group(1) == str(want).strip().lower() else 0.0

# end of kchk_code
