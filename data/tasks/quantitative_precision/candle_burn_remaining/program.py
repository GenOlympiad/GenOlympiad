# code: height_ratio_code
def candle_height_ratio(boxes):
    """Shorter candle height over taller candle height from the candle boxes."""
    geometry = (boxes or {}).get('geometry') or []
    heights = [abs(float(b[2]) - float(b[0])) for b in geometry]
    if len(heights) < 2 or max(heights) < 8.0:
        return {'ratio': None, 'degenerate': True, 'heights': heights}
    return {'ratio': round(min(heights) / max(heights), 4), 'degenerate': False,
            'h_short': round(min(heights), 1), 'h_tall': round(max(heights), 1)}

# end of height_ratio_code
