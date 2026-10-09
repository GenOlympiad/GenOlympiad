# shared code: code_6fc29f0a8a53
def extract_code(answer):
    """Pull the nine-character barcode text out of the answer, or None."""
    import re
    if answer is None or isinstance(answer, dict):
        return None
    text = str(answer).strip().upper()
    text = re.sub(r'[^0-9A-Z]', '', text)
    m = re.search(r'[0-9A-Z]{9}', text)
    return m.group(0) if m else (text if len(text) == 9 else None)

# end of code_6fc29f0a8a53

# code: pfx_code
def data_prefix_ok(read, want):
    """1 if the first eight characters read match the encoded data, else 0."""
    if not read or len(read) != 9:
        return 0.0
    return 1.0 if read[:8] == str(want) else 0.0

# end of pfx_code

# code: chk_code
def check_char_ok(read, full):
    """1 if the ninth character read matches the mod 43 check character, else 0."""
    if not read or len(read) != 9:
        return 0.0
    return 1.0 if read[8:] == str(full)[8:] else 0.0

# end of chk_code
