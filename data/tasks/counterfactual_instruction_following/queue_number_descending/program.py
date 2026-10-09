# code: run60_code
def run_down_from_60(cert, txt):
    """Check the confirmed ticket numbers form an unbroken run down from 60."""
    pairs = zip((txt or {}).get('answers') or [], (cert or {}).get('answers') or [])
    nums = [''.join(ch for ch in str(t) if ch.isdigit()) for t, y in pairs if str(y).strip().lower().startswith('y')]
    nums = sorted({int(v) for v in nums if v}, reverse=True)
    if not nums:
        return {'canon': 'no certified tickets', 'verdict': 'no cut-out was certified as a numbered ticket'}
    want = [60 - i for i in range(len(nums))]
    canon = 'consecutive run from 60' if nums == want else 'not a consecutive run from 60'
    return {'canon': canon, 'verdict': 'ticket numbers read: %s' % ', '.join(str(v) for v in nums)}

# end of run60_code

# code: linkscreen_code
def screen_continues_run(ticket_confirms, ticket_texts, screen_confirms, screen_texts):
    """Check the screen number is one below the lowest confirmed ticket number."""
    def vals(cert, txt):
        pairs = zip((txt or {}).get('answers') or [], (cert or {}).get('answers') or [])
        return [''.join(ch for ch in str(t) if ch.isdigit()) for t, y in pairs if str(y).strip().lower().startswith('y')]
    tickets = sorted({int(v) for v in vals(ticket_confirms, ticket_texts) if v})
    screen_numbers = [int(v) for v in vals(screen_confirms, screen_texts) if v]
    if not tickets or not screen_numbers:
        return {'canon': 'missing readings', 'verdict': 'tickets or screen gave no certified figure'}
    top = max(set(screen_numbers), key=screen_numbers.count)
    canon = 'screen continues the run' if top == tickets[0] - 1 else 'screen does not continue the run'
    return {'canon': canon, 'verdict': 'screen reads %d, lowest served ticket is %d' % (top, tickets[0])}

# end of linkscreen_code
