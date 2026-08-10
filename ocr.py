"""OCR wrapper (EasyOCR backend). Loads once, reads a cell, cleans numerics.
Engine is isolated here — grid/detect/capture never touch it, so swapping
backends only changes this file."""

import re

_reader = None

def _engine():
    global _reader
    if _reader is None:
        import easyocr
        # English covers the numeric columns; CPU mode on the 82FG.
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader

def read_raw(cell_bgr):
    import cv2
    # first pass: no upscaling (cleaner on normal cells)
    result = _engine().readtext(cell_bgr, detail=0)
    text = " ".join(result) if result else ""

    # fallback: only if the read looks failed (empty or a lone stray char),
    # retry upscaled — helps thin single digits without hurting normal cells
    if len(text.strip()) < 1:
        big = cv2.resize(cell_bgr, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        result = _engine().readtext(big, detail=0)
        text = " ".join(result) if result else ""

    return text

def clean_number(text):
    return re.sub(r"[^0-9.,]", "", text)