# shared code: code_0714a9a0e8e2
def read_semaphore_letters(figure_boxes, red, yel, reference, i=None):
    """Decode each signaller's two flag bearings into a letter and score it against the word."""
    import re as _re
    T = {"A": (225, 180), "B": (270, 180), "C": (315, 180), "D": (0, 180),
         "E": (180, 45), "F": (180, 90), "G": (180, 135), "H": (270, 225),
         "I": (0, 225), "J": (0, 90), "K": (225, 0), "L": (225, 45),
         "M": (225, 90), "N": (225, 135), "O": (270, 315), "P": (270, 0),
         "Q": (270, 45), "R": (270, 90), "S": (270, 135), "T": (315, 0),
         "U": (315, 45), "V": (0, 135), "W": (45, 90), "X": (45, 135),
         "Y": (315, 90), "Z": (135, 90)}
    CLOCK = [("10:30", 315), ("1:30", 45), ("4:30", 135), ("7:30", 225),
             ("12", 0), ("3", 90), ("6", 180), ("9", 270)]
    WORDS = [("upper left", 315), ("top left", 315), ("upper right", 45), ("top right", 45),
             ("lower left", 225), ("bottom left", 225), ("lower right", 135),
             ("bottom right", 135), ("straight up", 0), ("straight down", 180),
             ("up", 0), ("down", 180), ("left", 270), ("right", 90)]
    def bearing(a):
        s = str(a or "").lower().replace(":00", "")
        best, bp = None, 10 ** 9
        for tok, deg in CLOCK:
            m = _re.search(r"(?<![\d:])" + _re.escape(tok) + r"(?![\d:])", s)
            if m and m.start() < bp:
                bp, best = m.start(), deg
        if best is not None:
            return best
        for tok, deg in WORDS:
            if tok in s:
                return deg
        return None
    def decode(rb, lb, tol=25.0):
        if rb is None or lb is None:
            return None
        best, bd = None, 1e9
        for ch, (r, l) in T.items():
            dr = abs((rb - r + 180) % 360 - 180)
            dl = abs((lb - l + 180) % 360 - 180)
            if dr + dl < bd:
                bd, best = dr + dl, ch
        r, l = T[best]
        dr = abs((rb - r + 180) % 360 - 180)
        dl = abs((lb - l + 180) % 360 - 180)
        return best if (dr <= tol and dl <= tol) else None
    boxes = (figure_boxes or {}).get("geometry") or []
    red_answers = (red or {}).get("answers") or []
    yellow_answers = (yel or {}).get("answers") or []
    order = sorted(range(len(boxes)), key=lambda k: (boxes[k][1] + boxes[k][3]) / 2.0)
    letters, bearings = [], []
    for k in order:
        rb = bearing(red_answers[k]) if k < len(red_answers) else None
        lb = bearing(yellow_answers[k]) if k < len(yellow_answers) else None
        bearings.append([rb, lb])
        letters.append(decode(rb, lb))
    target_letters = [str((c[0] if isinstance(c, (list, tuple)) and c else c)).strip().upper()
           for c in (reference.get("letters") or [])]
    def letter_matches(k):
        return 1.0 if (k < len(letters) and letters[k] and letters[k] == target_letters[k]) else 0.0
    if i is None:
        frac = (sum(letter_matches(k) for k in range(len(target_letters))) / float(len(target_letters))) if target_letters else 0.0
    else:
        frac = letter_matches(i) if i < len(target_letters) else 0.0
    return {"frac": round(frac, 4), "letters": letters, "bearings": bearings,
            "word": "".join(c or "?" for c in letters), "n_read": len(boxes),
            "want": "".join(target_letters)}

# end of code_0714a9a0e8e2

# code: figures_code
def count_figures(figure_boxes, reference):
    """Score 1 when the number of signallers found equals the reference count."""
    boxes = (figure_boxes or {}).get("geometry") or []
    n = len(boxes)
    return {"frac": 1.0 if n == int(reference["n"]) else 0.0, "n_read": n, "n_want": int(reference["n"])}

# end of figures_code
