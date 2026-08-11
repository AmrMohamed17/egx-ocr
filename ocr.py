"""OCR wrappers (EasyOCR backend). Engines load once, lazily.
- read_raw: numeric cells (English digits), conditional upscale fallback.
- read_name: Arabic name cells, wider-crop fallback for short/faint names.
Grid/detect never touch the engine — swapping backends only changes this file."""
import re
import cv2

_reader_en = None
_reader_ar = None

def _engine_en():
    global _reader_en
    if _reader_en is None:
        import easyocr
        _reader_en = easyocr.Reader(["en"], gpu=False)
    return _reader_en

def _engine_ar():
    global _reader_ar
    if _reader_ar is None:
        import easyocr
        _reader_ar = easyocr.Reader(["ar"], gpu=False)
    return _reader_ar

# ---- numeric cells ----
def read_raw(cell_bgr):
    """Read a numeric cell. Conditional upscale only if the plain read is empty
    (helps thin single digits without corrupting normal cells)."""
    result = _engine_en().readtext(cell_bgr, detail=0)
    text = " ".join(result) if result else ""
    if len(text.strip()) < 1:
        big = cv2.resize(cell_bgr, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        result = _engine_en().readtext(big, detail=0)
        text = " ".join(result) if result else ""
    return text

# ---- name cells (Arabic) ----
def _keep_arabic(text):
    """Drop non-Arabic tokens (time fragments that bleed in from the wider crop)."""
    return " ".join(t for t in text.split() if re.search(r"[\u0600-\u06FF]", t))

def read_name(img, i, col_x, row_top, row_h, name_col=3):
    """Read the Arabic name cell for row i. Normal crop first; if empty, retry a
    wider crop (short right-aligned/faint names sit near the Name/Time boundary)
    and strip any time fragments that bleed in."""
    top = int(round(row_top + i * row_h))
    bot = int(round(row_top + (i + 1) * row_h))
    x0, x1 = col_x[name_col], col_x[name_col + 1]

    crop = img[top:bot, x0:x1]
    result = _engine_ar().readtext(crop, detail=0)
    text = " ".join(result) if result else ""

    if not text.strip():
        wide = img[top:bot, x0:461]           # extend right, past the boundary
        result = _engine_ar().readtext(wide, detail=0)
        text = _keep_arabic(" ".join(result) if result else "")

    return text