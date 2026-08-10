"""PaddleOCR wrapper. Loads the model once, reads a cell, cleans numerics.
DRAFT — verify with tools/smoke_ocr.py before building on this."""
import re

_ocr = None

def _engine():
    global _ocr
    if _ocr is None:
        from paddleocr import PaddleOCR
        # English/latin model is enough for the numeric columns.
        _ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
    return _ocr

def read_raw(cell_bgr):
    result = _engine().ocr(cell_bgr, cls=False)
    if not result or not result[0]:
        return ""
    # concatenate any text lines found in the cell
    return " ".join(line[1][0] for line in result[0])

def clean_number(text):
    """Keep digits, comma, dot. TODO: finalize per-column rules after smoke test."""
    t = re.sub(r"[^0-9.,]", "", text)
    return t