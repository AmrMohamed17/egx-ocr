"""Capture loop: grab the All Trades region, hash, save changed frames.
Currently capture-only. Stitching/OCR wire in next."""
import time, hashlib
from datetime import datetime
import numpy as np
import mss
from mss.tools import to_png
import config

def frame_hash(img):
    return hashlib.md5(img.tobytes()).hexdigest()

def run(duration_seconds=30):
    run_dir = config.CAPTURES_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    interval = 1.0 / config.TARGET_FPS
    last_hash = None
    total = changes = 0

    with mss.mss() as sct:
        start = time.time()
        while time.time() - start < duration_seconds:
            loop = time.time()
            sec = int(loop - start)
            grab = sct.grab(config.REGION)
            h = frame_hash(np.array(grab))
            total += 1
            changed = h != last_hash
            if changed:
                changes += 1
                last_hash = h
            if changed or not config.SAVE_ONLY_CHANGES:
                sec_dir = run_dir / f"sec_{sec:03d}"
                sec_dir.mkdir(exist_ok=True)
                ms = int((loop - start - sec) * 1000)
                to_png(grab.rgb, grab.size, output=str(sec_dir / f"{ms:03d}ms.png"))
            dt = time.time() - loop
            if dt < interval:
                time.sleep(interval - dt)

    el = time.time() - start
    print(f"{total} captures ({total/el:.1f}/s), {changes} changes "
          f"({changes/el:.1f}/s) -> {run_dir}")

if __name__ == "__main__":
    run(30)