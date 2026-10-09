# code: pitches_code
def read_bird_pitches(wires, birds, reference):
    """Read each bird, left to right, as the staff line or space nearest its centre height."""
    def centre_y(b):
        return (float(b[0]) + float(b[2])) / 2.0
    def centre_x(b):
        return (float(b[1]) + float(b[3])) / 2.0
    wire_heights = sorted(centre_y(b) for b in wires['geometry'])
    bands = [str(x) for x in reference['bands']]
    if len(wire_heights) < 2:
        return {'grid': [], 'degenerate': True,
                'verdict': 'fewer than two wires resolved -- no staff to read'}
    band_centres = []
    for k, wy in enumerate(wire_heights):
        band_centres.append(wy)
        if k + 1 < len(wire_heights):
            band_centres.append((wy + wire_heights[k + 1]) / 2.0)
    if len(band_centres) != len(bands):
        return {'grid': [], 'degenerate': True,
                'verdict': '%d wires give %d bands but the spec names %d'
                           % (len(wire_heights), len(band_centres), len(bands))}
    order = sorted(birds['geometry'], key=centre_x)
    read, bird_heights = [], []
    for b in order:
        y = centre_y(b)
        bird_heights.append(round(y, 1))
        idx = min(range(len(band_centres)), key=lambda i: abs(band_centres[i] - y))
        read.append(bands[idx])
    required = [str(x) for x in reference['melody']]
    matching = sum(1 for i in range(min(len(read), len(required))) if read[i] == required[i])
    return {'grid': [[p] for p in read], 'pitches': read, 'degenerate': False,
            'bird_ys': bird_heights, 'wire_ys': [round(w, 1) for w in wire_heights],
            'verdict': 'birds read left-to-right as %s vs required %s -> %d/%d notes on the '
                       'right line or space' % ('/'.join(read), '/'.join(required), matching,
                                                len(required))}

# end of pitches_code

# code: col_code
def melody_grid(notes):
    """Turn the required melody into a one-column grid, one note per row."""
    return [[str(x)] for x in (notes or [])]

# end of col_code
