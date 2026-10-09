# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code

import re
def floor_block_check(ans, k, first, last, pos, pos_room):
    """1 if the floor's room list has the right length, ends and room at the sampled place."""
    txt = ans
    if isinstance(ans, dict):
        a = ans.get("answers") or [None]
        txt = a[0]
    if txt is None:
        return {"frac": 0.0, "unreadable": 1.0, "why": "the block did not transcribe"}
    rooms = [int(x) for x in re.findall(r"\b\d{3}\b", str(txt))]
    if not rooms:
        return {"frac": 0.0, "unreadable": 1.0, "why": "no room numbers in the transcription",
                "read": str(txt)[:200]}
    ok = (len(rooms) == int(k) and rooms[0] == int(first) and rooms[-1] == int(last)
          and 1 <= int(pos) <= len(rooms) and rooms[int(pos) - 1] == int(pos_room))
    return {"frac": 1.0 if ok else 0.0, "unreadable": 0.0, "block": rooms,
            "want": [int(k), int(first), int(last), int(pos), int(pos_room)]}

# end of law_code
