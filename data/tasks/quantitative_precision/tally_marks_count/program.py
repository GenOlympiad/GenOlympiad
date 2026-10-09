# shared code: code_5cba035c8666
def tally_total(group_reads, loose_reads):
    """Total the tally as five per confirmed full group plus each confirmed loose stroke."""
    def yes(node):
        ans = (node or {}).get('answers') or []
        return sum(1 for a in ans if str(a).strip().lower().startswith('y'))
    full, loose = yes(group_reads), yes(loose_reads)
    return {'full': full, 'loose': loose, 'total': 5 * full + loose,
            'struct': [[full], [loose]]}

# end of code_5cba035c8666

# code: text_guard_code
def no_written_total(a, total_str):
    """Score 0 when the image writes the total or several numbers as text, else 1."""
    import re
    v = a.get('answers') if isinstance(a, dict) else None
    txt = str((v or [''])[0] or '') if v is not None else str(a or '')
    numbers = re.findall(r'\d+', txt)
    joined = ''.join(numbers)
    if total_str and len(total_str) >= 2 and (any(total_str in t for t in numbers)
                                              or total_str in joined):
        return 0.0
    pure = [t for t in numbers if re.fullmatch(r'\d{1,4}', t)]
    if len(pure) >= 2:
        return 0.0
    return 1.0

# end of text_guard_code
