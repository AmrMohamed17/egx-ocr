"""Central configuration. Every calibrated number and mode switch lives here."""
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent

# --- paths ---
CAPTURES_DIR     = BASE_DIR / "data" / "captures"
DB_DIR           = BASE_DIR / "data" / "db"
GROUND_TRUTH_DIR = BASE_DIR / "data" / "ground_truth"
GRID_CHECK_DIR   = BASE_DIR / "output" / "grid_checks"
REPORTS_DIR      = BASE_DIR / "output" / "reports"
FIXTURES_DIR     = BASE_DIR / "tests" / "fixtures"

# --- MODE SWITCHES ---
# READ_MODE: "full"      -> OCR every row each frame (max accuracy via voting)
#            "new_rows"   -> OCR only new rows via pixel-anchor (max speed)
READ_MODE = "full"
# USE_GPU: True on a CUDA machine (big speedup). False forces CPU.
USE_GPU   = False

# --- screen capture region (maximized All Trades window) ---
REGION = {"top": 95, "left": 8, "width": 545, "height": 820}

# --- calibrated grid (maximized window) ---
COL_X   = [50, 127, 208, 281, 431, 535]   # column boundaries, left -> right
ROW_TOP = 29
ROW_H   = 31.5
N_ROWS  = 25

COL_NAMES = ["%Change", "Vol", "Price", "Name", "Time"]
REQUIRED  = ["Vol", "Price", "Name", "Time"]

# --- capture / stitch ---
TARGET_FPS        = 15
SAVE_ONLY_CHANGES = True
MIN_RUN           = 4       # overlap rows to confirm anchor (tune live)

# --- detection thresholds ---
DARK_THRESHOLD = 120
CONTENT_FRAC   = 0.01

# --- name matching / validation ---
CHANGE_LIMIT = 20.0         # EGX daily move limit; |%change| beyond => misread

# --- canonical company-name list ---
NAMES_XLSX  = BASE_DIR / "data" / "co_names.xlsx"
NAMES_SHEET = "From Mistws"