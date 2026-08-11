"""Single per-frame entry point: read_frame(img) -> list of structured rows.
Consolidates grid crops + numeric OCR + %Change sign + name matching + torn
detection into one call. Everything BELOW this (pixels->rows) lives here or in
the modules it imports; everything ABOVE (rows->day: stitching, voting, dedup)
operates on the dicts this returns and never touches pixels or OCR."""
import re
import cv2
import numpy as np
import config
from grid import cell_crop
from ocr import read_raw, read_name
from names import match_name

# ---- per-column numeric cleaners (graduated from test_columns.py) ----
def _clean_pv(t):            # Vol / Price: digits, comma, dot
    return re.sub(r"[^0-9.,]", "", t)

def _clean_change_mag(t):    # %Change magnitude (sign comes from arrow color)
    return re.sub(r"[^0-9.]", "", t)

def _clean_time(t):
    d = re.sub(r"[^0-9]", "", t)
    return f"{d[0:2]}:{d[2:4]}:{d[4:6]}" if len(d) == 6 else ""   # "" = bad read

def _change_sign(cell):
    """-1 if the %Change arrow is red (down), +1 if blue (up). Reads only the
    left strip so the number's pixels don't pollute the color count."""
    strip = cell[:, 0:20]
    b = strip[:, :, 0].astype(int)
    g = strip[:, :, 1].astype(int)
    r = strip[:, :, 2].astype(int)
    red  = ((r > 120) & (r - g > 40) & (r - b > 40)).sum()
    blue = ((b > 120) & (b - r > 40) & (b - g > 20)).sum()
    return -1 if red > blue else 1

def _cell_has_content(cell):
    if cell.size == 0:
        return False
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    m = 2
    g = gray[m:-m, m:-m] if gray.shape[0] > 2*m and gray.shape[1] > 2*m else gray
    if g.size == 0:
        return False
    return (g < config.DARK_THRESHOLD).sum() / g.size > config.CONTENT_FRAC

def read_frame(img):
    """Return a list of N_ROWS dicts. Each row:
      {row, change, vol, price, name, name_score, time, status}
    status: 'ok'    - all required fields present & name matched
            'torn'  - some required cells present, others blank (mid-update)
            'empty' - no data (below the last trade in the window)
            'flag'  - read but a field failed validation (e.g. name below threshold)
    Numbers are strings as-OCR'd (cleaned); parsing to numeric happens later,
    at comparison time, so raw reads stay inspectable."""
    rows = []
    for i in range(config.N_ROWS):
        chg_cell = cell_crop(img, i, 0)
        vol_cell = cell_crop(img, i, 1)
        prc_cell = cell_crop(img, i, 2)
        tm_cell  = cell_crop(img, i, 4)

        # content presence per required column (for torn/empty classification)
        present = {
            "Vol":   _cell_has_content(vol_cell),
            "Price": _cell_has_content(prc_cell),
            "Name":  _cell_has_content(cell_crop(img, i, 3)),
            "Time":  _cell_has_content(tm_cell),
        }
        entirely_empty = not any(present.values())
        complete = all(present[c] for c in config.REQUIRED)

        if entirely_empty:
            rows.append({"row": i, "change": None, "vol": None, "price": None,
                         "name": None, "name_score": 0.0, "time": None,
                         "status": "empty"})
            continue

        # --- numbers ---
        mag = _clean_change_mag(read_raw(chg_cell))
        try:
            change = f"{_change_sign(chg_cell) * float(mag):.2f}" if mag else None
        except ValueError:
            change = None
        vol   = _clean_pv(read_raw(vol_cell)) or None
        price = _clean_pv(read_raw(prc_cell)) or None
        time  = _clean_time(read_raw(tm_cell)) or None

        # --- name ---
        name_ocr = read_name(img, i)
        name, name_score, name_ok = match_name(name_ocr)

        # --- status ---
        if not complete:
            status = "torn"
        elif not name_ok or price is None or time is None or vol is None:
            status = "flag"
        else:
            status = "ok"

        rows.append({"row": i, "change": change, "vol": vol, "price": price,
                     "name": name, "name_score": name_score, "time": time,
                     "status": status})
    return rows