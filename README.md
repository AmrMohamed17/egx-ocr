# EGX All-Trades OCR

Live OCR of the MIST "All Trades" window, stitched into a full-day file,
then compared against the app's exported history for an accuracy figure.

## Calibrated grid (source of truth: config.py)
- REGION: top=103 left=1073 w=560 h=816
- COL_X:  [5, 117, 200, 275, 425, 514]
- ROW_TOP=64  ROW_H=31.5  N_ROWS=23
- Columns: %Change | Vol | Price | Name | Time
Re-run tools/calibrate_grid.py if the window ever moves; update config.py only.

## Setup (Windows, run app-side)
    cd C:\egx-ocr
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
PaddlePaddle can be fussy on Windows; if `pip install paddlepaddle` fails,
install the CPU build from the official PaddlePaddle index, then re-run
tools/smoke_ocr.py. Do NOT build on ocr.py until the smoke test passes.

## Order of operations
1. tools/calibrate_grid.py  — set the grid (already done)
2. tools/check_cells.py     — verify torn/complete detection on a frame
3. tools/smoke_ocr.py       — confirm PaddleOCR reads Price/Vol cells
4. capture.py               — capture-only run
(stitch.py / compare.py come next)

## Notes
- Grid is hardcoded to a fixed window position. Lock or auto-detect the
  window before production, or a moved window = a day of garbage.
- Dedup by scroll position (overlap anchor), never by row content.