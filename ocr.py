"""OCR wrappers (EasyOCR). Engines load once. GPU controlled by config.USE_GPU.
- read_raw:  numeric cells (English), conditional upscale fallback.
- read_name: Arabic name cells, wider-crop fallback (fixed reach 461)."""
import re
import cv2
import config

_reader_en = None
_reader_ar = None

def _engine_en():
    global _reader_en
    if _reader_en is None:
        import easyocr
        _reader_en = easyocr.Reader(["en"], gpu=config.USE_GPU)
    return _reader_en

def _engine_ar():
    global _reader_ar
    if _reader_ar is None:
        import easyocr
        _reader_ar = easyocr.Reader(["ar"], gpu=config.USE_GPU)
    return _reader_ar

def read_raw(cell_bgr):
    result = _engine_en().readtext(cell_bgr, detail=0)
    text = " ".join(result) if result else ""
    if len(text.strip()) < 1:
        big = cv2.resize(cell_bgr, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        result = _engine_en().readtext(big, detail=0)
        text = " ".join(result) if result else ""
    return text

def _keep_arabic(text):
    return " ".join(t for t in text.split() if re.search(r"[\u0600-\u06FF]", t))

def read_name(img, i, name_col=3):
    from grid import row_bounds
    top, bot = row_bounds(i)
    x0 = config.COL_X[name_col]
    x1 = config.COL_X[name_col + 1]
    result = _engine_ar().readtext(img[top:bot, x0:x1], detail=0)
    text = " ".join(result) if result else ""
    if not text.strip():
        result = _engine_ar().readtext(img[top:bot, x0:461], detail=0)
        text = _keep_arabic(" ".join(result) if result else "")
    return text