import sys, pathlib, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import cv2, numpy as np, config
from grid import cell_crop
from ocr import read_raw

# ---- per-column cleaners ----
def clean_pv(t):        # Price / Vol: digits, comma, dot
    return re.sub(r"[^0-9.,]", "", t)

def clean_change_mag(t):  # %Change magnitude only (sign comes from color)
    return re.sub(r"[^0-9.]", "", t)

def clean_time(t):
    d = re.sub(r"[^0-9]", "", t)
    return f"{d[0:2]}:{d[2:4]}:{d[4:6]}" if len(d) == 6 else d  # else = bad read

# ---- %Change sign from the arrow color (left strip only) ----
def change_sign(cell):
    strip = cell[:, 0:20]        # arrow lives at far-left; number excluded
    b = strip[:,:,0].astype(int)
    g = strip[:,:,1].astype(int)
    r = strip[:,:,2].astype(int)
    red_mask  = (r > 120) & (r - g > 40) & (r - b > 40)
    blue_mask = (b > 120) & (b - r > 40) & (b - g > 20)
    rc, bc = int(red_mask.sum()), int(blue_mask.sum())
    # no arrow (e.g. 0.00 row) -> both ~0 -> default +1, sign is irrelevant there
    return (-1 if rc > bc else 1), rc, bc

# ---- main ----
IMG = str(config.FIXTURES_DIR / "torn.png")
img = cv2.imread(IMG)
if img is None:
    raise SystemExit(f"cannot read {IMG}")

# column indices: 0=%Change 1=Vol 2=Price 3=Name 4=Time
hdr = f"{'row':>3} | {'sign':>4} | {'red':>4} | {'blue':>4} | {'chg':>7} | {'Vol':>9} | {'Price':>8} | {'Time':>10}"
print(hdr)
print("-" * len(hdr))

for i in range(config.N_ROWS):
    chg_cell = cell_crop(img, i, 0)
    sign, rc, bc = change_sign(chg_cell)
    mag = clean_change_mag(read_raw(chg_cell))
    try:
        chg = f"{sign * float(mag):.2f}" if mag else ""
    except ValueError:
        chg = "?"

    vol   = clean_pv(read_raw(cell_crop(img, i, 1)))
    price = clean_pv(read_raw(cell_crop(img, i, 2)))
    tm    = clean_time(read_raw(cell_crop(img, i, 4)))

    print(f"{i:>3} | {sign:>4} | {rc:>4} | {bc:>4} | {chg:>7} | {vol:>9} | {price:>8} | {tm:>10}")