# code: helpers
from genolympiad.task_helpers import any_item_satisfies, join_box_reads
# end of helpers

# code: score_code
import re
def toks(x, words):
    s = str(x if x is not None else '').lower()
    return re.findall(r'\b(' + '|'.join(words) + r')\b', s)
def midflip_column_score(column_text, row_text, reference):
    """Score 1 when the lone differing column and lone 'yes' row match the reference ones."""
    column_words = toks(column_text, ['same', 'different'])
    row_words = toks(row_text, ['yes', 'no'])
    if not column_words or not row_words: return 0.0
    diff_columns = [i for i, w in enumerate(column_words) if w == 'different']
    yes_rows = [i for i, w in enumerate(row_words) if w == 'yes']
    if len(diff_columns) != 1 or len(yes_rows) != 1: return 0.0
    return 1.0 if (diff_columns[0] + 1 == int(reference['flip_col'])
                   and yes_rows[0] == int(reference['queried_row_index'])) else 0.0

# end of score_code
