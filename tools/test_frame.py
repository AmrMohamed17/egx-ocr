import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import cv2, config
from parse import read_frame

img = cv2.imread(str(config.FIXTURES_DIR / "region_test.png"))
rows = read_frame(img)

print(f"{'r':>2} | {'chg':>6} | {'vol':>8} | {'price':>7} | {'name':<18} | {'time':>8} | status")
print("-" * 75)
for row in rows:
    print(f"{row['row']:>2} | {str(row['change'] or ''):>6} | {str(row['vol'] or ''):>8} | "
          f"{str(row['price'] or ''):>7} | {str(row['name'] or '(flag)'):<18} | "
          f"{str(row['time'] or ''):>8} | {row['status']}")