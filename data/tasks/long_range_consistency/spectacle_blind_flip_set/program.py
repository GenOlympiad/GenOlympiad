# code: blind_fit_code
def count_blinds_set_right(keys, sets, want):
    """Count the blinds turned the way the line list requires, matched by key."""
    wanted = dict(p.split('=') for p in str(want).split('|') if p.count('=') == 1)
    key_answers = [str(a).strip().upper().replace(' ', '') for a in ((keys or {}).get('answers') or [])]
    set_answers = [str(a).strip().lower() for a in ((sets or {}).get('answers') or [])]
    n = 0
    for k, s in zip(key_answers, set_answers):
        wanted_state = str(wanted.get(k, '')).strip().lower()
        n += 1 if (wanted_state and s and wanted_state == s) else 0
    return {'n': n, 'seen': len(key_answers), 'verdict': '%d of the %d blinds are turned the way the line list requires' % (n, len(key_answers))}

# end of blind_fit_code

# code: cert_fit_code
def count_certificate_matches(keys, boxes, want):
    """Count certificate rows whose read entry agrees with the wanted value, by key."""
    wanted = dict(p.split('=') for p in str(want).split('|') if p.count('=') == 1)
    key_answers = [str(a).strip().upper().replace(' ', '') for a in ((keys or {}).get('answers') or [])]
    box_answers = [str(a).strip().lower() for a in ((boxes or {}).get('answers') or [])]
    n = 0
    for k, s in zip(key_answers, box_answers):
        wanted_state = str(wanted.get(k, '')).strip().lower()
        n += 1 if (wanted_state and s and wanted_state == s) else 0
    return {'n': n, 'seen': len(key_answers), 'verdict': '%d of the %d certificate rows agree with the steel' % (n, len(key_answers))}

# end of cert_fit_code
