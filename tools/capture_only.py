import sys, pathlib, time, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from datetime import datetime
import numpy as np, mss
from mss.tools import to_png
import config

def fhash(a): return hashlib.md5(a.tobytes()).hexdigest()

DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 15
run_dir = config.CAPTURES_DIR / datetime.now().strftime("burst_%Y%m%d_%H%M%S")
run_dir.mkdir(parents=True, exist_ok=True)
print(f"capturing {DURATION}s -> {run_dir}")

interval = 1.0 / config.TARGET_FPS
last = None; total = saved = 0
with mss.mss() as sct:
    start = time.time()
    while time.time() - start < DURATION:
        loop = time.time()
        grab = sct.grab(config.REGION)
        h = fhash(np.array(grab)); total += 1
        if h != last:
            last = h; saved += 1
            ms = int((loop - start) * 1000)
            to_png(grab.rgb, grab.size, output=str(run_dir / f"{saved:04d}_{ms:06d}ms.png"))
        dt = time.time() - loop
        if dt < interval: time.sleep(interval - dt)
print(f"captured {total}, saved {saved} changed frames")