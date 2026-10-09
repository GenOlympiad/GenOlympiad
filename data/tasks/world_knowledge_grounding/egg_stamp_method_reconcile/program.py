# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_housing_kind
def read_housing_view(kind, way_out):
    """Name the housing seen through the window and whether the hens have a way out."""
    def one(n):
        if isinstance(n, dict):
            a = n.get('answers') or []
            n = a[0] if a else None
        return '' if n is None else str(n).strip().lower()
    k, w = one(kind), one(way_out)
    if 'cage' in k:
        ins = 'cages'
    elif 'floor' in k or 'litter' in k or 'perch' in k:
        ins = 'floor'
    elif 'grass' in k or 'outdoor' in k or 'open air' in k:
        ins = 'grass'
    else:
        ins = 'unread'
    out = 'yes' if w.startswith('y') else ('no' if w.startswith('n') and 'none' not in w
                                           else 'unread')
    return {'s': 'inside=%s,outside=%s' % (ins, out),
            'verdict': 'the window shows %s with a way out reading %s' % (ins, out)}

# end of code_housing_kind

# shared code: code_shell_stamp
def read_shell_stamp(code):
    """The shell stamp code read, lower cased with only letters and digits, or none."""
    def one(n):
        if isinstance(n, dict):
            a = n.get('answers') or []
            n = a[0] if a else None
        return '' if n is None else str(n)
    raw = one(code)
    flat = ''.join(c for c in raw.lower() if c.isalnum())
    if not flat or flat in ('none', 'nothing', 'na'):
        flat = ''
    return {'s': flat or 'none', 'raw': raw,
            'verdict': 'the shell stamp reads %s' % (raw.strip() or 'nothing')}

# end of code_shell_stamp
