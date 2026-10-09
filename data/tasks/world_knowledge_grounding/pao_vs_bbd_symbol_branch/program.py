# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: monyr_code
import re
def read_month_year(node):
    """Read a month and year from the date answer, swapping them if they look reversed."""
    answer = ((node or {}).get('answers') or [''])[0]
    numbers = [int(x) for x in re.findall(r'\d+', str(answer))]
    if len(numbers) < 2:
        return {'norm': 'unread', 'verdict': 'no month and year could be read'}
    month, year = numbers[0], numbers[1]
    if month > 12 >= year:
        month, year = year, month
    if year < 100:
        year = year + 2000
    return {'norm': '%d-%d' % (month, year), 'verdict': 'read month %d of year %d' % (month, year)}

# end of monyr_code
