# code: seq_frac_code
def _norm(x):
    import re
    s = str(x).strip().upper().replace('\u266f','#').replace('\u266d','B')
    m = re.match(r'([A-G])\s*([#B]?)', s)
    if not m: return ''
    letter, acc = m.group(1), m.group(2)
    CHROMA=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    FLAT={'DB':'C#','EB':'D#','GB':'F#','AB':'G#','BB':'A#','CB':'B','FB':'E'}
    tok = letter+acc
    if acc=='B':
        tok = FLAT.get(letter+acc, tok)
    return tok
def note_match_share(seq, reference):
    """The share of notes matching the transposed reference, capped at 0.25 on any miss."""
    target_notes = [_norm(x) for x in reference['tgt_seq']]
    read_notes = []
    if isinstance(seq,(list,tuple)):
        read_notes = [_norm(x) for x in seq]
    else:
        import re
        read_notes = [_norm(t) for t in re.split(r'[\s,;]+', str(seq)) if t.strip()]
    no_read = (len([g for g in read_notes if g]) == 0)
    ok = sum(1 for i,a in enumerate(target_notes) if i < len(read_notes) and read_notes[i]==a)
    frac = round(ok/len(target_notes),4) if target_notes else 0.0
    if ok < len(target_notes): frac = min(frac, 0.25)
    return {'frac': frac, 'no_read': no_read}

# end of seq_frac_code
