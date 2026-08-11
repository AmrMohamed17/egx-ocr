# EGX All-Trades Live OCR

Live OCR of the MIST "All Trades" window (Egyptian Exchange). Captures the
maximized window during market hours (9:00–2:30), reads each row (%Change, Vol,
Price, Name, Time), stitches frames into one ordered de-duplicated day, and is
built to be compared against the app's exported history for an accuracy figure.

## Requirements
- Python 3.12
- Runs on the machine DISPLAYING the trading app (screen capture is local).
- The "All Trades" window must be **maximized and fully visible** while running.

## Setup (CPU)
    python -m venv .venv
    .venv\Scripts\activate            # Windows
    pip install -r requirements.txt

EasyOCR model files must be in `~/.EasyOCR/model/` (auto-download, or place
manually if the network blocks it):
- `craft_mlt_25k.pth` (detection, shared)
- `english_g2.pth`    (numbers)
- `arabic_g1.pth`     (names)

Canonical company list: place the names xlsx at `data/co_names.xlsx`
(sheet `From Mistws`, one column of names).

## Setup (GPU / CUDA) — for the fast box
Install CUDA-enabled PyTorch FIRST (EasyOCR won't pull it automatically):
    # from https://pytorch.org — pick your CUDA version, e.g.:
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
    pip install -r requirements.txt
Then set `USE_GPU = True` in config.py. Verify:
    python -c "import torch; print(torch.cuda.is_available())"   # must print True

## Mode switches (config.py)
- `READ_MODE = "full"`     — OCR every row each frame. Max accuracy (voting
  repairs flagged rows across frames). Slower.
- `READ_MODE = "new_rows"` — OCR only new rows via pixel-anchor. Max speed.
  No cross-frame voting.
- `USE_GPU = True/False`   — CUDA acceleration on/off.

Recommended: on the GPU box, try `full` first (best accuracy). If it can't hit
`TARGET_FPS`, switch to `new_rows`.

## Calibration (only if the window geometry changes)
All coordinates live in config.py. If the window moves/resizes, recapture one
frame and re-run:
    python tools\calibrate_grid.py
Update config.py with the printed COL_X / ROW_TOP / ROW_H / N_ROWS.
Current calibration is for the MAXIMIZED window at 1920x1080.

## Run
    python run_live.py            # runs until Ctrl+C
    python run_live.py 60         # runs 60 seconds (shakeout)
Output: per-frame log (read ms, new rows, overlap breaks), a summary
(avg read ms, sustainable fps, breaks), and `day.txt` (the assembled day).
Every changed frame is saved as PNG under data/captures/live_* for replay.

## Pipeline
capture (mss) -> read_frame/read_rows (parse.py) -> stitch (stitch.py) -> day
Reading: grid.py (geometry) · ocr.py (EasyOCR) · names.py (fuzzy match to
canonical list) · validate.py (range checks) · anchor.py (pixel overlap, new_rows mode).

## Status / TODO
- [x] Capture, grid, torn/complete/empty detection
- [x] Numeric columns (%Change sign via arrow color, Vol, Price, Time)
- [x] Arabic name matching (fuzzy WRatio vs canonical list; faint-name fallback)
- [x] Stitching (content-anchor + voting) / pixel-anchor (new_rows)
- [x] Validation rules (out-of-range catch)
- [ ] Live validation on GPU box: measure fps, tune MIN_RUN, confirm no overlap loss
- [ ] compare.py: accuracy vs exported day-history (needs a real export)

## Notes
- Grid is fixed to the maximized window position. If it ever runs un-maximized,
  output is garbage — ensure the window is maximized before starting.
- Dedup is by scroll position (overlap anchor), never by row content
  (genuine duplicate trades exist).