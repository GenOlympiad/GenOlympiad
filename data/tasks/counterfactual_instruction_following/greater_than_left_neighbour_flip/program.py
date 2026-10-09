# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: orient_code
def read_ticket_orientations(node):
    """Whether each price ticket stands upright or inverted, left to right."""
    states = []
    for a in (node or {}).get('answers') or []:
        s = str(a).strip().lower()
        states.append('inverted' if s.startswith('i') else ('upright' if s.startswith('u') else '?'))
    return {'s': ','.join(states), 'verdict': 'the rail stands %s from left to right' % ','.join(states)}

# end of orient_code

# code: money_code
def read_ticket_prices(node):
    """The decimal price read on each ticket, left to right."""
    import re
    prices = []
    for a in (node or {}).get('answers') or []:
        m = re.search(r'\d+\.\d+', str(a))
        prices.append(m.group(0) if m else '?')
    return {'s': ','.join(prices), 'verdict': 'the rail reads %s from left to right' % ','.join(prices)}

# end of money_code
