"""Classify each row as complete / torn / empty from a captured frame."""
import cv2
import config
from grid import cell_crop, row_bounds

def cell_has_content(cell):
    if cell.size == 0:
        return False
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    m = 2
    g = gray[m:-m, m:-m] if gray.shape[0] > 2*m and gray.shape[1] > 2*m else gray
    if g.size == 0:
        return False
    frac = (g < config.DARK_THRESHOLD).sum() / g.size
    return frac > config.CONTENT_FRAC

def analyze(img):
    rows = []
    for i in range(config.N_ROWS):
        present = {name: cell_has_content(cell_crop(img, i, c))
                   for c, name in enumerate(config.COL_NAMES)}
        complete = all(present[r] for r in config.REQUIRED)
        empty = not any(present.values())
        rows.append({"i": i, "present": present,
                     "complete": complete, "empty": empty})
    return rows