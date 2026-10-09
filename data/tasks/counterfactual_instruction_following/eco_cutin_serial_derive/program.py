# shared code: code_pair_serial
def pair_serials_with_stamps(serial_reads, stamp_reads):
    """Pair each work ticket serial with its stamp, sorted by serial."""
    normalise = lambda s: ''.join(ch for ch in str(s).lower() if ch.isalnum())
    serials = [normalise(x) for x in (serial_reads or {}).get('answers') or []]
    stamps = [normalise(x) for x in (stamp_reads or {}).get('answers') or []]
    rows = sorted(zip(serials, stamps))
    txt = '|'.join('%s:%s' % (k, v) for k, v in rows)
    return {'txt': txt, 'n': len(rows), 'verdict': 'cards paired serial:stamp -> %s' % txt}

# end of code_pair_serial

# shared code: code_norm_word
def normalise_reading(node):
    """Lowercase the first answer and keep only its letters and digits."""
    raw_answer = str(((node or {}).get('answers') or [''])[0])
    t = ''.join(ch for ch in raw_answer.lower() if ch.isalnum())
    return {'txt': t, 'verdict': 'normalised reading -> %s' % t}

# end of code_norm_word
