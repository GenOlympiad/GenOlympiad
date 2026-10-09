# shared code: code_1ba107f0f383
def standings_column(transcript, teams, column):
    """Read each listed team's wins or losses from the transcribed standings table."""
    import re
    text = transcript.get('answers') if isinstance(transcript, dict) else transcript
    if isinstance(text, (list, tuple)):
        text = text[0] if text else None
    if not text:
        return {'per_team': [], 'no_read': True, 'rows': []}

    def norm(s):
        return re.sub(r'[^a-z0-9]', '', str(s).lower())

    rows = []
    for line in str(text).splitlines():
        line = str(line).replace('|', ' ').replace('\t', ' ').strip()
        if not line or re.match(r'^[-=_\s]+$', line):
            continue
        line = re.sub(r'\d*\.\d+', ' ', line)
        line = re.sub(r'\d+\s*%', ' ', line)
        line = re.sub(r'^\s*\d{1,2}\s*[.):\-]?\s+(?=[A-Za-z])', '', line)
        name_match = re.match(r"^\s*([A-Za-z][A-Za-z.'\- ]{1,40}?)\s+(?=\d)", line)
        if not name_match:
            continue
        nums = [int(x) for x in re.findall(r'(?<!\d)\d{1,3}(?!\d)', line[name_match.end():])]
        if norm(name_match.group(1)) and len(nums) >= 2:
            rows.append((norm(name_match.group(1)), nums))

    def key(t):
        parts = [p for p in str(t).replace('.', ' ').split() if p]
        last = norm(parts[-1]) if parts else norm(t)
        return last if len(last) >= 3 else norm(t)

    col_index = 0 if str(column).lower() == 'wins' else 1
    per_team = []
    for t in (teams or []):
        k = key(t)
        value = None
        for name, nums in rows:
            if k and (k in name or (len(k) >= 4 and k[:5] in name)):
                value = nums[col_index] if col_index < len(nums) else None
                break
        per_team.append(value)
    n = len(teams or [])
    found = [v for v in per_team if v is not None]
    return {'per_team': per_team, 'rows': rows, 'n_missing': n - len(found),
            'no_read': bool(n and len(found) < n)}

# end of code_1ba107f0f383
