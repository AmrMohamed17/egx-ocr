"""Central configuration. Every calibrated number lives here and nowhere else.
If the trading window moves or you run on a different machine, re-run
tools/calibrate_grid.py and update ONLY this file."""
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent

# --- paths ---
CAPTURES_DIR     = BASE_DIR / "data" / "captures"
DB_DIR           = BASE_DIR / "data" / "db"
GROUND_TRUTH_DIR = BASE_DIR / "data" / "ground_truth"
GRID_CHECK_DIR   = BASE_DIR / "output" / "grid_checks"
REPORTS_DIR      = BASE_DIR / "output" / "reports"
FIXTURES_DIR     = BASE_DIR / "tests" / "fixtures"

# --- screen capture region (All Trades window on screen) ---
# NOTE: screen coordinates. Valid only while the window stays put.
REGION = {"top": 95, "left": 8, "width": 545, "height": 820}

# --- calibrated grid (maximized window, from tools/calibrate_grid.py) ---
COL_X   = [50, 127, 208, 281, 431, 535]   # column boundaries, left -> right
ROW_TOP = 29                              # y of first data row top
ROW_H   = 31.5                            # row height in px
N_ROWS  = 25                              # rows to read per frame

COL_NAMES = ["%Change", "Vol", "Price", "Name", "Time"]
# columns that must be non-empty for a row to count as complete:
REQUIRED  = ["Vol", "Price", "Name", "Time"]

# --- capture loop ---
TARGET_FPS        = 5       # captures per second
SAVE_ONLY_CHANGES = True    # skip saving identical frames

# --- content / torn detection ---
DARK_THRESHOLD = 120        # pixel < this = "text ink"
CONTENT_FRAC   = 0.01       # >1% ink in a cell = has content

# --- canonical company-name list (app's exact spellings) ---
NAMES_XLSX  = BASE_DIR / "data" / "co_names.xlsx"
NAMES_SHEET = "From Mistws"