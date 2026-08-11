"""Per-frame reading. read_frame() reads all rows; read_rows() reads a subset
(new-rows-only path). Both apply validation and set a status per row."""
import re
import cv2
import config
from grid import cell_crop
from ocr import read_raw, read_name
from names import match_name
from validate import validate_row

def _clean_pv(t):         return re.sub(r"[^0-9.,]", "", t)
def _clean_change_mag(t): return re.sub(r"[^0-9.]", "", t)
def _clean_time(t):
    d = re.sub(r"[^0-9]", "", t)
    return f"{d[0:2]}:{d[2:4]}:{d[4:6]}" if len(d) == 6 else ""

def _change_sign(cell):
    strip = cell[:, 0:20]
    b, g, r = strip[:,:,0].astype(int), strip[:,:,1].astype(int), strip[:,:,2].astype(int)
    red  = ((r > 120) & (r - g > 40) & (r - b > 40)).sum()
    blue = ((b > 120) & (b - r > 40) & (b - g > 20)).sum()
    return -1 if red > blue else 1

def _cell_has_content(cell):
    if cell.size == 0: return False
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    m = 2
    g = gray[m:-m, m:-m] if gray.shape[0] > 2*m and gray.shape[1] > 2*m else gray
    if g.size == 0: return False
    return (g < config.DARK_THRESHOLD).sum() / g.size > config.CONTENT_FRAC

def _read_one_row(img, i):
    chg = cell_crop(img, i, 0); vol = cell_crop(img, i, 1)
    prc = cell_crop(img, i, 2); tm  = cell_crop(img, i, 4)
    present = {"Vol": _cell_has_content(vol), "Price": _cell_has_content(prc),
               "Name": _cell_has_content(cell_crop(img, i, 3)), "Time": _cell_has_content(tm)}
    if not any(present.values()):
        return {"row": i, "change": None, "vol": None, "price": None, "name": None,
                "name_score": 0.0, "time": None, "status": "empty", "reasons": []}
    mag = _clean_change_mag(read_raw(chg))
    try: change = f"{_change_sign(chg) * float(mag):.2f}" if mag else None
    except ValueError: change = None
    row = {"row": i, "change": change,
           "vol": _clean_pv(read_raw(vol)) or None,
           "price": _clean_pv(read_raw(prc)) or None,
           "time": _clean_time(read_raw(tm)) or None}
    name, score, _ = match_name(read_name(img, i))
    row["name"] = name; row["name_score"] = score
    complete = all(present[c] for c in config.REQUIRED)
    ok, reasons = validate_row(row); row["reasons"] = reasons
    row["status"] = "torn" if not complete else ("ok" if ok else "flag")
    return row

def read_frame(img):
    return [_read_one_row(img, i) for i in range(config.N_ROWS)]

def read_rows(img, indices):
    return {i: _read_one_row(img, i) for i in indices}