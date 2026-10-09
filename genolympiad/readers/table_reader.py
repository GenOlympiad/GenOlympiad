"""Read tables in an image with OCR."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import re
import logging

log = logging.getLogger(__name__)

_RAPID = None


def _rapid():
    global _RAPID
    if _RAPID is None:
        from rapidocr_onnxruntime import RapidOCR
        _RAPID = RapidOCR()
    return _RAPID


@dataclass
class TableGrid:
    rows: list[list[str]]
    bbox: tuple[int, int, int, int]

    @property
    def shape(self) -> tuple[int, int]:
        return (len(self.rows), max((len(r) for r in self.rows), default=0))


@dataclass
class TableReadResult:
    tables: list[TableGrid] = field(default_factory=list)
    words: list[tuple[int, int, str, float]] = field(default_factory=list)
    boxes: list[tuple[int, int, int, int, str, float]] = field(default_factory=list)
    abstain: bool = False
    reason: str = ""


def read_tables(img_path: str, *, borderless: bool = False,
                min_conf: int = 40) -> TableReadResult:
    out = TableReadResult()
    try:
        from img2table.document import Image as I2TImage
        from img2table.ocr import EasyOCR
        doc = I2TImage(img_path)
        ocr = EasyOCR(lang=["en"])
        tabs = doc.extract_tables(ocr=ocr, implicit_rows=False,
                                  borderless_tables=borderless, min_confidence=min_conf)
        for t in tabs:
            rows = []
            for _, cells in t.content.items():
                rows.append([(c.value or "").strip() for c in cells])
            b = t.bbox
            out.tables.append(TableGrid(rows=rows, bbox=(b.x1, b.y1, b.x2, b.y2)))
    except Exception as e:
        log.debug("error ignored in read_tables", exc_info=True)
        out.reason = f"img2table:{type(e).__name__}:{e}"

    try:
        res, _ = _rapid()(img_path)
        for box, txt, conf in (res or []):
            cx = int(sum(p[0] for p in box) / 4)
            cy = int(sum(p[1] for p in box) / 4)
            out.words.append((cx, cy, txt.strip(), float(conf)))
            xs = [p[0] for p in box]; ys = [p[1] for p in box]
            out.boxes.append((int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)),
                              txt.strip(), float(conf)))
    except Exception as e:
        log.debug("error ignored in read_tables", exc_info=True)
        out.reason = (out.reason + f" rapidocr:{type(e).__name__}:{e}").strip()

    if not out.tables and not out.words:
        out.abstain = True
        out.reason = out.reason or "no_table_no_text"
    return out


def _num(s: str) -> Optional[float]:
    m = re.search(r"-?\d[\d,]*\.?\d*", (s or "").replace(" ", ""))
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        log.debug("error ignored in _num", exc_info=True)
        return None
