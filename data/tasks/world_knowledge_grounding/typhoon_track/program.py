# code: parse_code
import re
def parse_advisory(raw):
    """Read the storm name and heading from the advisory text, if a storm is active."""
    out = {'active': 0, 'name': None, 'head8': None}
    text = re.sub(r'<[^>]+>', ' ', str(raw or ''))
    m = re.search(r'(?:Tropical Storm|Hurricane|Tropical Depression|Post-Tropical Cyclone)\s+([A-Za-z\-]+)\s+Advisory', text, re.I)
    if not m:
        return out
    storm_name = m.group(1).strip()
    out['active'] = 1
    out['name'] = storm_name
    out['name_lower'] = storm_name.lower()
    movement_match = re.search(r'PRESENT MOVEMENT\.\.\.\s*[A-Z]{1,3}\s*OR\s*(\d{1,3})\s*DEGREES', text)
    if not movement_match:
        out['head8'] = None
        out['head_deg'] = None
        return out
    deg = float(movement_match.group(1))
    dirs = ['N','NE','E','SE','S','SW','W','NW']
    out['head8'] = dirs[int((deg % 360) / 45.0 + 0.5) % 8]
    out['head_deg'] = deg
    return out
# end of parse_code
