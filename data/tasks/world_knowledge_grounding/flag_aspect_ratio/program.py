# shared code: code_cd7b5b9252fe
def aspect_class(width_read, height_read, target_cls):
    """Score 1 when the read width-to-height ratio falls in the target shape class."""
    import re
    def to_number(x):
        m = re.search(r'([0-9]+\.?[0-9]*)', str(x));
        return float(m.group(1)) if m else None
    w, h = to_number(width_read), to_number(height_read)
    if not w or not h or h == 0: return 0.0
    ratio = w / h
    if ratio < 1.2: shape_class = 'square'
    elif ratio < 1.9: shape_class = 'normal'
    else: shape_class = 'ultrawide'
    return 1.0 if shape_class == str(target_cls) else 0.0

# end of code_cd7b5b9252fe
