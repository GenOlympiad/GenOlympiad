# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code

import re
def _norm(s):
    return re.sub(r"[^A-Z0-9]", "", str(s).upper())
_ISO = re.compile(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b")
_LOOSE = re.compile(r"\b(\d{4})\s+(\d{1,2})\s+(\d{1,2})\b")
def _rows(txt):
    out = []
    for line in str(txt).splitlines():
        s = line.strip()
        if not s:
            continue
        up = s.upper()
        kind = "BORROW" if "BORROW" in up else ("RETURN" if "RETURN" in up else None)
        if kind is None:
            continue
        m = _ISO.search(s) or _LOOSE.search(s)
        date = (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None
        rest = (s[:m.start()] + " " + s[m.end():]) if m else s
        rest = re.sub(r"(?i)\b(borrow|return)\b", " ", rest)
        rest = re.sub(r"(?i)^\s*(row|no|line|#)?\s*\d{1,3}\s*[.):]\s*", " ", rest.strip())
        out.append((_norm(rest), kind, date))
    return out
def copy_borrow_return_chain(ans, copy):
    """1 if the copy has four events alternating borrow and return with rising dates."""
    txt = ans
    if isinstance(ans, dict):
        a = ans.get("answers") or [None]
        txt = a[0]
    if txt is None:
        return {"frac": 0.0, "unreadable": 1.0, "why": "the ledger did not transcribe"}
    rows = _rows(txt)
    if not rows:
        return {"frac": 0.0, "unreadable": 1.0, "why": "no transaction rows in the transcription",
                "read": str(txt)[:300]}
    want = _norm(copy)
    hits = [(k, d) for c, k, d in rows if c == want]
    if len(hits) != 4:
        return {"frac": 0.0, "unreadable": 0.0, "n_hits": len(hits),
                "why": "the sampled copy does not carry exactly four events"}
    order = ["BORROW", "RETURN", "BORROW", "RETURN"]
    for (k, d), w in zip(hits, order):
        if k != w or d is None:
            return {"frac": 0.0, "unreadable": 0.0, "seq": [h[0] for h in hits],
                    "why": "the four events do not alternate borrow/return"}
    ds = [d for k, d in hits]
    for a, b in zip(ds, ds[1:]):
        if not (b > a):
            return {"frac": 0.0, "unreadable": 0.0, "dates": ds,
                    "why": "the four dates are not strictly increasing"}
    return {"frac": 1.0, "unreadable": 0.0, "dates": ds, "seq": [h[0] for h in hits]}

# end of law_code
