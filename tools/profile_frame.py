import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import cv2, config
from grid import cell_crop
from ocr import read_raw, read_name, _engine_en, _engine_ar

img = cv2.imread(str(config.FIXTURES_DIR / "region_test.png"))

# warm up both engines (first call loads the model — don't count that)
_engine_en(); _engine_ar()
read_raw(cell_crop(img, 0, 1)); read_name(img, 0)

# time one numeric cell
t=time.time(); read_raw(cell_crop(img, 0, 1)); print(f"1 numeric cell: {(time.time()-t)*1000:.0f}ms")
# time one name cell
t=time.time(); read_name(img, 0); print(f"1 name cell:    {(time.time()-t)*1000:.0f}ms")
# time a full row (4 numeric + 1 name)
t=time.time()
for c in (0,1,2,4): read_raw(cell_crop(img,0,c))
read_name(img,0)
print(f"1 full row:     {(time.time()-t)*1000:.0f}ms")
# extrapolate
print(f"=> 25 rows ~ {((time.time()-t)*1000)*25:.0f}ms")