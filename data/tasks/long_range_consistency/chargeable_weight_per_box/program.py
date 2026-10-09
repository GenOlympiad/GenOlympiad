# code: basis_code
def charge_basis_by_piece(piece_reads, basis_reads):
    """Pair each piece number with the letter of the basis it is charged on."""
    nums = [''.join(c for c in str(x) if c.isdigit()) for x in (piece_reads or {}).get('answers') or []]
    letters = [''.join(c for c in str(x) if c.isalpha()).upper()[:1] for x in (basis_reads or {}).get('answers') or []]
    rows = {}
    for i, key in enumerate(nums):
        if key:
            rows[key] = letters[i] if i < len(letters) and letters[i] else '?'
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'verdict': 'the piece lines are charged on %s' % (seq or 'nothing')}

# end of basis_code

# code: quoted_code
def quoted_weight(node):
    """The chargeable weight figure written on the quotation."""
    raw = str((((node or {}).get('answers') or [''])[0]) or '')
    keep = ''.join(c for c in raw if c.isdigit() or c == '.').strip('.')
    return {'txt': keep or 'none', 'verdict': 'the quotation is written up at %s kg' % (keep or 'nothing')}

# end of quoted_code
