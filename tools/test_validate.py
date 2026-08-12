import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import cv2, config
from parse import read_frame
from validate import validate_row

img = cv2.imread(str(config.FIXTURES_DIR / "region_test.png"))
rows = read_frame(img)

print(f"{'r':>2} | {'chg':>6} | {'vol':>7} | {'price':>7} | {'time':>8} | {'status':>5} | reasons")
print("-" * 80)
flagged = 0
for r in rows:
    ok, reasons = validate_row(r)
    if not ok and r["status"] != "empty":
        flagged += 1
    reason_str = ", ".join(reasons) if reasons else "-"
    print(f"{r['row']:>2} | {str(r['change'] or ''):>6} | {str(r['vol'] or ''):>7} | "
          f"{str(r['price'] or ''):>7} | {str(r['time'] or ''):>8} | "
          f"{r['status']:>5} | {reason_str}")

print(f"\n{flagged} rows failed validation")
print("Check: are any FLAGGED rows actually CORRECT in the image? "
      "(that would be a false positive to fix)")