"""Threaded live runner. Thread 1 captures every changed frame at max speed
(never blocked by OCR). Thread 2 drains the queue through read_frame + stitch.
On GPU, processing keeps pace; on CPU it lags but loses nothing (frames queued
and saved). This is the architecture that catches every RENDERED state — the
app skips some states itself, which no capture can recover, but we never add
loss by blocking capture on OCR."""
import time, hashlib, signal, sys, threading, queue
from datetime import datetime
import numpy as np
import mss
from mss.tools import to_png
import config
from parse import read_frame
from stitch import Stitcher

def fhash(a):
    return hashlib.md5(a.tobytes()).hexdigest()

def capture_thread(q, run_dir, stop, stats):
    """Grab region as fast as possible; enqueue + save each CHANGED frame."""
    last_hash = None
    with mss.mss() as sct:
        start = time.time()
        while not stop.is_set():
            grab = sct.grab(config.REGION)
            arr = np.array(grab)
            stats["captured"] += 1
            h = fhash(arr)
            if h != last_hash:
                last_hash = h
                stats["changed"] += 1
                ms = int((time.time() - start) * 1000)
                fname = f"{stats['changed']:05d}_{ms:08d}.png"
                to_png(grab.rgb, grab.size, output=str(run_dir / fname))
                # enqueue a copy of the BGR image for processing
                q.put((stats["changed"], arr[:, :, :3].copy()))
            # tiny sleep to avoid pegging a core at 100% for no gain
            time.sleep(0.005)   # ~200fps ceiling; real limit is grab time
    q.put(None)   # sentinel: tell processor to stop

def process_thread(q, st, stop, stats):
    """Drain the queue: read_frame + stitch each captured frame in order."""
    while True:
        item = q.get()
        if item is None:
            break
        idx, img = item
        try:
            t0 = time.time()
            st.add_frame(read_frame(img))
            stats["proc_ms_sum"] += (time.time() - t0) * 1000
            stats["processed"] += 1
            stats["qdepth"] = q.qsize()
        except Exception as e:
            import traceback
            print(f"\n!!! process error on frame {idx}: {e}")
            traceback.print_exc()
            stats["qdepth"] = q.qsize()

def main(duration_s=None):
    run_dir = config.CAPTURES_DIR / datetime.now().strftime("thread_%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"MODE=full  GPU={config.USE_GPU}  ->  {run_dir}")

    q = queue.Queue(maxsize=0)     # unbounded: never drop a captured frame
    st = Stitcher(min_run=config.MIN_RUN)
    stop = threading.Event()
    stats = {"captured": 0, "changed": 0, "processed": 0,
             "proc_ms_sum": 0.0, "qdepth": 0}

    cap = threading.Thread(target=capture_thread, args=(q, run_dir, stop, stats), daemon=True)
    proc = threading.Thread(target=process_thread, args=(q, st, stop, stats), daemon=True)

    def on_sigint(sig, frm):
        stop.set()
    signal.signal(signal.SIGINT, on_sigint)

    STARTUP_DELAY = 2
    for s in range(STARTUP_DELAY, 0, -1):
        print(f"starting in {s}...")
        time.sleep(1)

    cap.start()
    proc.start()

    start = time.time()
    try:
        while True:
            if duration_s and time.time() - start > duration_s:
                stop.set()
            if stop.is_set():
                break
            time.sleep(1.0)
            el = time.time() - start
            avg = stats["proc_ms_sum"] / max(stats["processed"], 1)
            print(f"[{el:4.0f}s] captured={stats['captured']:5d} "
                  f"changed={stats['changed']:4d} processed={stats['processed']:4d} "
                  f"qdepth={stats['qdepth']:4d} avg_proc={avg:5.0f}ms "
                  f"day={len(st.day):5d} broken={st.broken}")
    except KeyboardInterrupt:
        stop.set()

    stop.set()
    print("\ndraining queue (finishing OCR on captured frames)...")
    proc.join(timeout=300)     # let processing finish the backlog
    cap.join(timeout=5)

    el = time.time() - start
    print(f"\n--- done ---")
    print(f"ran {el:.0f}s  captured={stats['captured']} changed={stats['changed']} "
          f"processed={stats['processed']}")
    if stats["changed"] > stats["processed"]:
        print(f"WARNING: {stats['changed']-stats['processed']} frames captured but "
              f"not processed (OCR too slow — GPU needed for live). Frames are "
              f"saved; re-run process_saved.py to finish them.")
    print(f"assembled day: {len(st.day)} trades, breaks: {st.broken}")

    out = run_dir / "day.txt"
    with open(out, "w", encoding="utf-8") as f:
        for r in st.day:
            f.write(f"{r['time']}\t{r['change']}\t{r['vol']}\t{r['price']}\t"
                    f"{r['name']}\t[{r['status']}]\n")
    print(f"day -> {out}")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)