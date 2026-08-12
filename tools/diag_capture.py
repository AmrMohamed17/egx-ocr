import sys, pathlib, time, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from datetime import datetime
import numpy as np, mss
from mss.tools import to_png
import config

DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 3
run_dir = config.CAPTURES_DIR / datetime.now().strftime("raw_%H%M%S")
run_dir.mkdir(parents=True, exist_ok=True)

times = []
hashes = []
with mss.mss() as sct:
    start = time.time()
    n = 0
    while time.time() - start < DURATION:
        t = time.time()
        grab = sct.grab(config.REGION)
        arr = np.array(grab)
        h = hashlib.md5(arr.tobytes()).hexdigest()[:8]
        times.append(t - start)
        hashes.append(h)
        # save EVERY frame, no dedup
        to_png(grab.rgb, grab.size, output=str(run_dir / f"{n:04d}_{int((t-start)*1000):05d}.png"))
        n += 1

# analysis
print(f"captured {n} frames in {DURATION}s = {n/DURATION:.0f}/s (NO dedup, NO sleep)")
print(f"saved -> {run_dir}\n")
# how many were actually distinct, and the gaps between changes
distinct = 0
last = None
change_times = []
for t, h in zip(times, hashes):
    if h != last:
        distinct += 1
        change_times.append(t)
        last = h
print(f"distinct frames: {distinct} / {n}")
if len(change_times) > 1:
    gaps = [change_times[i+1]-change_times[i] for i in range(len(change_times)-1)]
    print(f"gaps between changes: min={min(gaps)*1000:.0f}ms  "
          f"max={max(gaps)*1000:.0f}ms  avg={sum(gaps)/len(gaps)*1000:.0f}ms")
    print(f"implied change rate: {1/(sum(gaps)/len(gaps)):.1f}/s")