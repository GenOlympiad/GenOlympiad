# code: dark_letters_code
def dark_letters(cert, letter, state):
    """List the confirmed binned vials whose square matches the tone of its ring."""
    confirmed = [str(x).strip().lower().startswith('y') for x in ((cert or {}).get('answers') or [])]
    letter_reads = [str(x).strip().strip('.').upper()[:1] for x in ((letter or {}).get('answers') or [])]
    states = [str(x).strip().lower() for x in ((state or {}).get('answers') or [])]
    n = min(len(confirmed), len(letter_reads), len(states))
    keep = sorted({letter_reads[i] for i in range(n) if confirmed[i] and letter_reads[i] and states[i].startswith('m')})
    return {'letters': ','.join(keep), 'n': len(keep),
            'verdict': 'binned vials whose square matches its ring: %s'
                       % (','.join(keep) or 'none')}

# end of dark_letters_code

# code: light_count_code
def light_count(cert, state):
    """Count the confirmed tray vials whose square reads paler than its ring."""
    confirmed = [str(x).strip().lower().startswith('y') for x in ((cert or {}).get('answers') or [])]
    states = [str(x).strip().lower() for x in ((state or {}).get('answers') or [])]
    n = sum(1 for i in range(min(len(confirmed), len(states))) if confirmed[i] and states[i].startswith('p'))
    return {'n': n, 'asked': len(states),
            'verdict': '%d confirmed vials in the tray read paler than their own ring' % n}

# end of light_count_code
