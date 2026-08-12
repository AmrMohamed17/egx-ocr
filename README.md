# EGX All-Trades Live OCR

Live OCR of the MIST "All Trades" window (Egyptian Exchange). Captures the
maximized window during market hours, reads each row (%Change, Vol, Price, Name,
Time), and stitches frames into one ordered, de-duplicated day.

Capture and OCR run in **separate threads**: capture grabs every changed frame at
~35 fps and never blocks; OCR drains a queue behind it. On a CUDA GPU, OCR keeps
pace and the pipeline is live. On CPU, OCR lags ~20 s/frame (frames are still
saved and can be processed offline).

---

## Known constraint (read this first)

The MIST "All Trades" window **repaints in jumps** during high-volume bursts —
it does not render every intermediate trade. Screen capture can only read what is
drawn, so trades that scroll past between repaints are not recoverable by any
capture rate or OCR engine. In calm periods frames overlap cleanly and coverage
is complete; loss is concentrated in bursts. Target accuracy (~90-95% vs the
day's export) assumes bursts are infrequent. This is a data-source limit, not an
OCR limit. The real number must be measured against an export (see `compare.py`,
TODO).

---

## 1. Requirements

- **Python 3.12**
- **An NVIDIA GPU with CUDA** (for live speed). CPU works but cannot keep pace live.
- The machine must **display the trading app** — screen capture is local. MIST
  must run and be visible on the same machine that runs this code. A headless
  cloud GPU with no MIST window will NOT work.

## 2. Get the code

```
git clone https://github.com/AmrMohamed17/egx-ocr.git
cd egx-ocr
```

## 3. Python environment

```
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux:
source .venv/bin/activate
```

## 4. Install CUDA PyTorch FIRST (critical)

EasyOCR will NOT pull a CUDA-enabled PyTorch on its own — install it explicitly
before anything else, matching your machine's CUDA version. Check your CUDA
version with `nvidia-smi` (top-right of the output), then pick the matching
index URL from https://pytorch.org. Example for CUDA 12.1:

```
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

Then verify CUDA is actually available BEFORE continuing:

```
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

This MUST print `CUDA: True`. If it prints `False`, stop and fix the torch
install — the GPU will not be used otherwise.

## 5. Install the rest

```
pip install -r requirements.txt
```

## 6. EasyOCR model files

They auto-download on first run. If the network blocks it (SSL cert errors),
download in a browser, unzip, and place the `.pth` files in the EasyOCR model
folder (`~/.EasyOCR/model/` on Linux, `C:\Users\<you>\.EasyOCR\model\` on Windows):

- Detection (shared): **craft_mlt_25k.pth**
  https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip
- Numbers (English): **english_g2.pth**
  https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/english_g2.zip
- Names (Arabic): **arabic_g1.pth**
  https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/arabic.zip

Model hub: https://www.jaided.ai/easyocr/modelhub/

## 7. Canonical company list

Place the names spreadsheet at **`data/co_names.xlsx`** (sheet `From Mistws`,
one column of company names in the app's exact spellings). Required for name
matching. (Committed with the repo unless removed for confidentiality.)

## 8. Configure (config.py)

```python
USE_GPU   = True        # MUST be True on the GPU machine
READ_MODE = "full"      # "full" = max accuracy (voting). "new_rows" = max speed.
TARGET_FPS = 15         # capture ceiling; capture runs as fast as it can up to this
MIN_RUN   = 4           # overlap rows to confirm the stitch anchor
```

**The grid coordinates (REGION, COL_X, ROW_TOP, ROW_H, N_ROWS) are calibrated for
the MAXIMIZED window at 1920x1080.** If the GPU machine has a different resolution
or the window looks different, you MUST re-calibrate (see section 11) or every
crop lands on the wrong pixels.

## 9. Prepare the trading window

- Open MIST, open the **All Trades** window, **maximize it**, keep it fully
  visible and in the foreground.
- It must stay maximized and unmoved for the whole session — the grid is fixed to
  that geometry.

## 10. Run

```
python run_threaded.py 30       # 30-second test (2s startup countdown first)
python run_threaded.py          # runs until Ctrl+C (a full session)
```

During the 2-second countdown, click over to the MIST window so it is in front
when capture begins.

**Watch `qdepth` in the output — it is the key number:**
- `qdepth` near 0 and `processed` = `changed`  -> OCR keeps pace -> **LIVE-CAPABLE.**
- `qdepth` climbing  -> OCR too slow (CPU, or GPU not actually engaged — recheck
  step 4).

Output: per-second stats, and `data/captures/thread_*/day.txt` — the assembled
day (time, %change, vol, price, name, status per trade). Every changed frame is
also saved as PNG in that folder.

Note: `broken` is only meaningful when OCR keeps pace. On slow processing,
consecutive *processed* frames are far apart in time and won't overlap, inflating
`broken` — that is an artifact, not a stitch failure. On GPU it should be ~0.

## 11. Re-calibrate (only if geometry differs)

If crops are misaligned (wrong resolution, different window):
```
python tools\capture_only.py 5          # capture a few frames
# save one as tests/fixtures/region_test.png (crop to REGION), then:
python tools\calibrate_grid.py          # drag lines, press 'p', copy numbers
```
Paste the printed COL_X / ROW_TOP / ROW_H / N_ROWS into config.py.

## 12. Offline processing (CPU fallback / backlog)

If OCR fell behind and frames are queued but unprocessed, grind through the saved
frames offline (speed irrelevant):
```
python tools\process_saved.py thread_YYYYMMDD_HHMMSS
```

---

## Pipeline

```
capture (mss, thread 1)  ->  queue  ->  read_frame (thread 2)  ->  stitch  ->  day.txt
```
- `config.py`   — all calibration + mode switches
- `grid.py`     — cell geometry
- `parse.py`    — read_frame(): crops + OCR + validation per row
- `ocr.py`      — EasyOCR wrappers (English numbers, Arabic names), GPU toggle
- `names.py`    — fuzzy-match Arabic name to canonical list (rapidfuzz WRatio)
- `validate.py` — range checks (catches gross misreads)
- `stitch.py`   — overlap anchor + voting (repairs flagged rows across frames)
- `anchor.py`   — pixel overlap detection (new_rows mode only)
- `run_threaded.py` — the live runner

## Accuracy design

Errors are prevented by layers, not by a perfect OCR:
1. **Validation** — out-of-range values (|%change|>20, price<=0, bad time) flagged.
2. **Voting (full mode)** — each row read in several frames; misreads outvoted.
3. **Overlap** — a row flagged in one frame is recovered from adjacent frames.

A flagged row is a *caught* error (recovered or excluded), not an emitted one.

## Status

- [x] Capture (threaded, ~35fps, lossless), grid, torn/empty detection
- [x] Numbers (%change sign via arrow color, vol, price, time)
- [x] Arabic name matching + faint-name fallback
- [x] Stitching + voting, validation
- [x] Threaded runner (decoupling proven on CPU)
- [ ] GPU run: confirm qdepth stays low (live-capable) — DO THIS ON THE GPU BOX
- [ ] Tune MIN_RUN against live overlap; confirm broken ~0 on GPU
- [ ] compare.py: accuracy vs exported day-history (needs a real export)