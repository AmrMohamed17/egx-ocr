import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import cv2, config
from grid import cell_crop

# Separate Arabic reader — do NOT reuse the English one in ocr.py.
import easyocr
print("Loading Arabic reader (may download model on first run)...")
reader = easyocr.Reader(["ar"], gpu=False)

IMG = str(config.FIXTURES_DIR / "torn.png")
img = cv2.imread(IMG)
if img is None:
    raise SystemExit(f"cannot read {IMG}")

print(f"\n{'row':>3} | raw Arabic OCR of Name cell")
print("-" * 50)
for i in range(config.N_ROWS):
    cell = cell_crop(img, i, 3)          # column 3 = Name
    result = reader.readtext(cell, detail=0)
    text = " ".join(result) if result else "(empty)"
    print(f"{i:>3} | {text}")