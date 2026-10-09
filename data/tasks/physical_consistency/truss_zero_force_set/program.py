# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# code: main_code
def norm(x):
    s = str(x).strip().lower()
    if 'red' in s:
        return 'red'
    if 'grey' in s or 'gray' in s or 'black' in s or 'dark' in s:
        return 'grey'
    return s
def red_set_exact(seq, labels, want):
    """1 if exactly the zero-force members are painted red, else 0."""
    colours = [norm(t) for t in (seq or [])]
    if len(colours) < len(labels):
        return 0.0
    red_members = set(l for l, c in zip(labels, colours) if c == 'red')
    return 1.0 if red_members == set(want) else 0.0

# end of main_code

# code: main_code_2
def norm(x):
    s = str(x).strip().lower()
    if 'red' in s:
        return 'red'
    if 'grey' in s or 'gray' in s or 'black' in s or 'dark' in s:
        return 'grey'
    return s
def member_colour_share(seq, labels, want):
    """The share of members painted red if zero-force and grey otherwise."""
    colours = [norm(t) for t in (seq or [])]
    if len(colours) < len(labels):
        return 0.0
    wanted = set(want)
    n_right = 0
    for l, c in zip(labels, colours):
        expect = 'red' if l in wanted else 'grey'
        if c == expect:
            n_right += 1
    return round(n_right / float(len(labels)), 4)

# end of main_code_2
