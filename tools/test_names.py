import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import cv2, config
from grid import cell_crop
from names import match_name
import easyocr

reader = easyocr.Reader(["ar"], gpu=False)
img = cv2.imread(str(config.FIXTURES_DIR / "clean.png"))

print(f"{'row':>3} | {'canonical match':<22} | score | ok")
print("-" * 45)
for i in range(config.N_ROWS):
    cell = cell_crop(img, i, 3)
    raw = reader.readtext(cell, detail=0)
    ocr = " ".join(raw) if raw else ""
    name, score, ok = match_name(ocr)
    disp = name if name else "(flagged)"
    print(f"{i:>3} | {disp:<22} | {score:5.0f} | {'ok' if ok else 'FLAG'}")