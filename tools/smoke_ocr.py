import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import cv2, config
from grid import cell_crop
from ocr import read_raw, clean_number

# reads the Price(2) and Vol(1) cells of the first few rows of a fixture
IMG = str(config.FIXTURES_DIR / "clean.png")
img = cv2.imread(IMG)
if img is None: raise SystemExit(f"cannot read {IMG} — put a fixture there first")
print("Loading PaddleOCR (first run downloads models)...")
for i in range(6):
    vol   = clean_number(read_raw(cell_crop(img, i, 1)))
    price = clean_number(read_raw(cell_crop(img, i, 2)))
    print(f"row {i}: Vol={vol!r}  Price={price!r}")