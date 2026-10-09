# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, to_float
# end of helpers

# code: decode_payload_set_code

def decode_payload_set(image_path, targets):
    """Decode the QR codes on the sheet and check that every expected payload was found."""
    import cv2, numpy as np
    img = cv2.imread(str(image_path))
    if img is None:
        return {"n_decoded": 0, "found": [], "all_ok": 0.0}
    qr_reader = cv2.QRCodeDetector()
    found = set()
    try:
        ok, decoded, pts, _ = qr_reader.detectAndDecodeMulti(img)
        if ok:
            for s in decoded:
                if s:
                    found.add(str(s).strip())
    except Exception:
        pass
    H, W = img.shape[:2]
    for row in range(3):
        for col in range(2):
            y0 = int(row * H / 3); y1 = int((row + 1) * H / 3)
            x0 = int(col * W / 2); x1 = int((col + 1) * W / 2)
            part = img[y0:y1, x0:x1]
            try:
                s, p, _ = qr_reader.detectAndDecode(part)
                if s:
                    found.add(str(s).strip())
            except Exception:
                pass
    tgt = set(str(t).strip() for t in targets)
    all_ok = 1.0 if tgt and tgt.issubset(found) else 0.0
    return {"n_decoded": len(found), "found": sorted(found), "all_ok": all_ok}

# end of decode_payload_set_code
