import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import cv2, config
from detect import analyze
from grid import row_bounds

IMG = sys.argv[1] if len(sys.argv) > 1 else str(config.FIXTURES_DIR / "clean.png")
img = cv2.imread(IMG)
if img is None: raise SystemExit(f"cannot read {IMG}")
rows = analyze(img); vis = img.copy()
for r in rows:
    top, bot = row_bounds(r["i"])
    if r["empty"]:      color, label = (160,160,160), "empty"
    elif r["complete"]: color, label = (0,160,0), "ok"
    else:
        miss = [n for n,p in r["present"].items() if not p]
        color, label = (0,0,255), "TORN:"+",".join(miss)
    cv2.rectangle(vis, (config.COL_X[0], top), (config.COL_X[-1], bot), color, 1)
    cv2.putText(vis, label, (config.COL_X[-1]+3, bot-6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.32, color, 1)
config.GRID_CHECK_DIR.mkdir(parents=True, exist_ok=True)
out = config.GRID_CHECK_DIR / (pathlib.Path(IMG).stem + "_check.png")
cv2.imwrite(str(out), vis)
ok = sum(r["complete"] and not r["empty"] for r in rows)
torn = sum((not r["complete"]) and not r["empty"] for r in rows)
print(f"{ok} ok, {torn} torn -> {out}")