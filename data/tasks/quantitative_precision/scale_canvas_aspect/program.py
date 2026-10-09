# code: aspect_code
def canvas_aspect(canvas_node, full_image):
    """The width to height ratio of the canvas box, measured in pixels."""
    b = [float(v) for v in canvas_node['geometry'][0]]
    W, H = full_image.size
    w = abs(b[3] - b[1]) * float(W) / 1000.0
    h = abs(b[2] - b[0]) * float(H) / 1000.0
    if w < 8.0 or h < 8.0:
        return {'aspect': None, 'degenerate': True}
    return {'aspect': round(w / h, 4), 'w_px': round(w, 1), 'h_px': round(h, 1),
            'img': [W, H], 'degenerate': False}

# end of aspect_code
