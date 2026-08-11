import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import cv2, config
from ocr import read_name
from names import match_name

img = cv2.imread(str(config.FIXTURES_DIR / "region_test.png"))

print(f"{'row':>3} | {'match':<22} | score | ok")
print("-" * 45)
for i in range(config.N_ROWS):
    ocr = read_name(img, i, config.COL_X, config.ROW_TOP, config.ROW_H)
    name, score, ok = match_name(ocr)
    print(f"{i:>3} | {(name or '(flagged)'):<22} | {score:5.0f} | {'ok' if ok else 'FLAG'}")