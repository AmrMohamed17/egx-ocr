"""Pixel overlap detection for new-rows mode: how many top rows are NEW,
found by comparing row-strip images (no OCR). tol absorbs highlight flicker."""
import numpy as np
import config
from grid import row_bounds

def _strip(img, i):
    top, bot = row_bounds(i)
    return img[top:bot, config.COL_X[0]:config.COL_X[-1]]

def _eq(a, b, tol=3.0):
    if a.shape != b.shape: return False
    return np.abs(a.astype(np.int16) - b.astype(np.int16)).mean() <= tol

def count_new_rows(prev_img, new_img, min_run=4, max_new=None):
    n = config.N_ROWS
    if max_new is None: max_new = n - min_run
    prev = [_strip(prev_img, r) for r in range(n)]
    best = (None, 0)
    for k in range(0, max_new + 1):
        run = 0
        while k + run < n and run < n and _eq(_strip(new_img, k + run), prev[run]):
            run += 1
        if run >= min_run: return (k, run)
        if run > best[1]: best = (k, run)
    return (None, best[1])