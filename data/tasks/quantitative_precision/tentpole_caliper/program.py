# shared code: code_f992e2703a44
def take(rd):
    import re
    a = (rd or {}).get('answers') or []
    t = a[0] if a else None
    if t is None:
        return {'value': None, 'no_read': True}
    s = str(t).replace(',', '')
    m = re.findall(r'-?\d+(?:\.\d+)?', s)
    if not m:
        return {'value': None, 'no_read': True}
    return {'value': float(m[-1]), 'no_read': False}

# end of code_f992e2703a44

# code: take_vernier_code
def take_vernier(reads):
    """The last number in the vernier scale reading, or a refusal if there is none."""
    import re
    answers = (reads or {}).get('answers') or []
    first_answer = answers[0] if answers else None
    if first_answer is None:
        return {'value': None, 'no_read': True, 'refused': True}
    s = str(first_answer).replace(',', '')
    numbers = re.findall(r'-?\d+(?:\.\d+)?', s)
    if not numbers:
        return {'value': None, 'no_read': True, 'refused': True}
    return {'value': float(numbers[-1]), 'no_read': False}

# end of take_vernier_code

# code: take_main_code
def take_main(reads):
    """The last number in the main scale reading, or a refusal if there is none."""
    import re
    answers = (reads or {}).get('answers') or []
    first_answer = answers[0] if answers else None
    if first_answer is None:
        return {'value': None, 'no_read': True, 'refused': True}
    s = str(first_answer).replace(',', '')
    numbers = re.findall(r'-?\d+(?:\.\d+)?', s)
    if not numbers:
        return {'value': None, 'no_read': True, 'refused': True}
    return {'value': float(numbers[-1]), 'no_read': False}

# end of take_main_code
