# shared code: code_0a4a01868eb0
def width_height(p):
    try:
        with open(p, 'rb') as f:
            head = f.read(32)
        if head[:8] == b'\x89PNG\r\n\x1a\n':
            import struct
            w, h = struct.unpack('>II', head[16:24])
            if w > 0 and h > 0:
                return float(w), float(h)
    except Exception:
        pass
    return 1.0, 1.0


def coin_value_cents(coin_boxes, colour_reads, image):
    """Sort the coins by colour and relative size and total their value in cents."""
    geometry = (coin_boxes or {}).get('geometry') or []
    answers = (colour_reads or {}).get('answers') or []
    W, H = width_height(image) if isinstance(image, str) else (1.0, 1.0)
    coins = []
    for i, b in enumerate(geometry):
        a = str(answers[i]).strip().lower() if i < len(answers) and answers[i] is not None else ''
        if a.startswith('copper'):
            colour = 'copper'
        elif a.startswith('silver'):
            colour = 'silver'
        else:
            continue
        ymin, xmin, ymax, xmax = [float(v) for v in b[:4]]
        d = 0.5 * (abs(xmax - xmin) * W + abs(ymax - ymin) * H) / 1000.0
        coins.append((colour, d))
    n = len(coins)
    if n == 0:
        return {'cents': None, 'n': 0, 'n_quarter': None, 'n_penny': None,
                'n_dime': None, 'n_nickel': None, 'asked': len(geometry), 'degenerate': True}
    silver = [d for c, d in coins if c == 'silver']
    counts = {'quarter': 0, 'nickel': 0, 'dime': 0, 'penny': n - len(silver)}
    if silver:
        dmax = max(silver)
        ladder = (('quarter', 1.0), ('nickel', 0.8743), ('dime', 0.7382))
        for d in silver:
            r = (d / dmax) if dmax > 0 else 1.0
            best, best_gap = 'quarter', 9e9
            for name, ref in ladder:
                if abs(r - ref) < best_gap:
                    best, best_gap = name, abs(r - ref)
            counts[best] += 1
    cents = 25 * counts['quarter'] + 10 * counts['dime'] + 5 * counts['nickel'] + counts['penny']
    return {'cents': cents, 'n': n, 'n_quarter': counts['quarter'], 'n_penny': counts['penny'],
            'n_dime': counts['dime'], 'n_nickel': counts['nickel'], 'asked': len(geometry),
            'degenerate': False}

# end of code_0a4a01868eb0
