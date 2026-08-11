"""Live runner. Honors config.READ_MODE ('full' | 'new_rows') and config.USE_GPU.
Saves every changed frame (replay insurance). Ctrl+C or pass seconds to stop."""
import time, hashlib, signal, sys
from datetime import datetime
import numpy as np
import mss
from mss.tools import to_png
import config
from parse import read_frame, read_rows
from stitch import Stitcher

def fhash(a): return hashlib.md5(a.tobytes()).hexdigest()

def main(duration_s=None):
    run_dir = config.CAPTURES_DIR / datetime.now().strftime("live_%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"MODE={config.READ_MODE}  GPU={config.USE_GPU}  ->  {run_dir}")
    st = Stitcher(min_run=config.MIN_RUN)
    interval = 1.0 / config.TARGET_FPS
    last_hash, prev_img = None, None
    total = changed = 0; read_ms_sum = 0.0
    stop = {"f": False}
    signal.signal(signal.SIGINT, lambda s,f: stop.__setitem__("f", True))

    if config.READ_MODE == "new_rows":
        from anchor import count_new_rows

    with mss.mss() as sct:
        start = time.time()
        while not stop["f"]:
            if duration_s and time.time()-start > duration_s: break
            loop = time.time()
            grab = sct.grab(config.REGION); arr = np.array(grab); total += 1
            h = fhash(arr)
            if h == last_hash:
                dt = time.time()-loop
                if dt < interval: time.sleep(interval-dt)
                continue
            last_hash = h; changed += 1
            img = arr[:, :, :3]
            ts = datetime.now().strftime("%H%M%S_")+f"{int((loop-start)*1000)%1000:03d}"
            to_png(grab.rgb, grab.size, output=str(run_dir/f"{ts}.png"))

            t0 = time.time()
            if config.READ_MODE == "full" or prev_img is None:
                st.add_frame(read_frame(img)); added = "full"
            else:
                k, run = count_new_rows(prev_img, img, min_run=config.MIN_RUN)
                if k is None:
                    st.broken += 1; st.prev = None
                    st.add_frame(read_frame(img)); added = "resync"
                else:
                    new = read_rows(img, list(range(k)))
                    st.add_new_rows([new.get(i) for i in range(k)]); added = k
            read_ms = (time.time()-t0)*1000; read_ms_sum += read_ms
            prev_img = img
            print(f"[{changed:4d}] {read_ms:6.0f}ms  +{str(added):>6}  "
                  f"day={len(st.day):5d}  broken={st.broken}")
            dt = time.time()-loop
            if dt < interval: time.sleep(interval-dt)

    el = time.time()-start
    print(f"\nran {el:.0f}s  captures={total}({total/el:.1f}/s)  changed={changed}({changed/el:.1f}/s)")
    if changed: print(f"avg read {read_ms_sum/changed:.0f}ms  ~{1000/max(read_ms_sum/changed,1):.1f}fps")
    print(f"day={len(st.day)}  breaks={st.broken}")
    out = run_dir/"day.txt"
    with open(out,"w",encoding="utf-8") as f:
        for r in st.day:
            f.write(f"{r['time']}\t{r['change']}\t{r['vol']}\t{r['price']}\t{r['name']}\t[{r['status']}]\n")
    print(f"day -> {out}")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv)>1 else None)