# shared code: code_cue_times
def cue_times_clear(node):
    """Parse each cue's in and out times and check that cues neither run backwards nor overlap."""
    spans = []
    for raw in (node or {}).get('answers') or []:
        nums = [int(x) for x in ''.join(c if c.isdigit() else ' ' for c in str(raw)).split()]
        if len(nums) >= 8:
            spans.append([nums[0] * 3600000 + nums[1] * 60000 + nums[2] * 1000 + nums[3],
                         nums[4] * 3600000 + nums[5] * 60000 + nums[6] * 1000 + nums[7]])
    spans.sort()
    ok = all(v[1] > v[0] for v in spans) and all(spans[i + 1][0] >= spans[i][1]
                                                for i in range(len(spans) - 1))
    return {'txt': 'clear' if spans and ok else 'clash', 'n': len(spans),
            'opening': min([v[0] for v in spans] or [-1])}

# end of code_cue_times

# shared code: code_lastwords
def closing_words(texts, marks):
    """The last three words of the cue with the latest out time."""
    texts_read = texts.get('answers') if isinstance(texts, dict) else None
    marks_read = marks.get('answers') if isinstance(marks, dict) else None
    texts_read = list(texts_read) if isinstance(texts_read, (list, tuple)) else []
    marks_read = list(marks_read) if isinstance(marks_read, (list, tuple)) else []
    best, best_index = None, -1
    for i, raw in enumerate(marks_read):
        nums = [int(x) for x in ''.join(c if c.isdigit() else ' ' for c in str(raw)).split()]
        if len(nums) >= 8:
            out = nums[4] * 3600000 + nums[5] * 60000 + nums[6] * 1000 + nums[7]
            if best is None or out > best:
                best, best_index = out, i
    if 0 <= best_index < len(texts_read):
        row = str(texts_read[best_index])
    else:
        row = str(texts_read[-1]) if texts_read else ''
    txt = ''.join(c if c.isalpha() else ' ' for c in row.lower())
    tail = ' '.join(txt.split()[-3:])
    return {'txt': tail, 'n': len(texts_read),
            'verdict': 'the cue with the latest out time closes on %s' % (tail or 'nothing')}

# end of code_lastwords

# code: measure_code
def line_limits(node, words):
    """Whether the cues carry the wanted number of words in at most two lines of at most 37 characters."""
    worst, most_lines, n_words = 0, 0, 0
    for raw in (node or {}).get('answers') or []:
        parts = [p.strip() for p in str(raw).split('/') if p.strip()]
        most_lines = max(most_lines, len(parts))
        n_words += len(' '.join(parts).split())
        for part in parts:
            worst = max(worst, len(part))
    ok = n_words == words and 0 < most_lines <= 2 and worst <= 37
    return {'txt': 'within' if ok else 'over', 'worst': worst, 'lines': most_lines, 'words': n_words,
            'verdict': '%d words on screen, longest line %d characters, most lines a cue %d' % (n_words, worst, most_lines)}

# end of measure_code

# code: rate_code
def reading_rate_in_band(texts_read, times_read):
    """Whether every cue shows between 12 and 17 characters per second."""
    texts = [str(x) for x in ((texts_read or {}).get('answers') or [])]
    times = [str(x) for x in ((times_read or {}).get('answers') or [])]
    ok = []
    for i in range(min(len(texts), len(times))):
        n = [int(x) for x in ''.join(c if c.isdigit() else ' ' for c in times[i]).split()] + [0] * 8
        span = (n[4] * 3600000 + n[5] * 60000 + n[6] * 1000 + n[7]) - (n[0] * 3600000 + n[1] * 60000 + n[2] * 1000 + n[3])
        chars = len(texts[i].replace('/', ' '))
        ok.append(1 if span > 0 and 12.0 <= chars * 1000.0 / span <= 17.0 else 0)
    return {'txt': 'inband' if ok and min(ok) == 1 else 'outband', 'n': len(ok)}

# end of rate_code
