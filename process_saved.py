"""Offline processor: replay saved consecutive frames through the full
read + stitch pipeline and produce the assembled day. Speed doesn't matter
here — this proves correctness. On GPU this same logic runs fast enough live."""
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import cv2, config
from parse import read_frame, read_rows
from stitch import Stitcher

folder = sys.argv[1] if len(sys.argv) > 1 else None
if not folder:
    print("usage: python tools\\process_saved.py <capture_folder_name>")
    print("folders:", [p.name for p in config.CAPTURES_DIR.glob("*") if p.is_dir()])
    raise SystemExit

cap_dir = config.CAPTURES_DIR / folder
frames = sorted(cap_dir.glob("*.png"))
print(f"processing {len(frames)} frames from {folder}  MODE={config.READ_MODE}\n")

st = Stitcher(min_run=config.MIN_RUN)
prev_img = None
if config.READ_MODE == "new_rows":
    from anchor import count_new_rows

t_start = time.time()
for idx, f in enumerate(frames):
    img = cv2.imread(str(f))[:, :, :3]
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
    prev_img = img
    print(f"[{idx+1:3d}/{len(frames)}] {f.name}  {(time.time()-t0)*1000:5.0f}ms  "
          f"+{str(added):>6}  day={len(st.day):5d}  broken={st.broken}")

el = time.time() - t_start
print(f"\nprocessed {len(frames)} frames in {el:.0f}s")
print(f"assembled day: {len(st.day)} trades, overlap breaks: {st.broken}")

out = cap_dir / "day.txt"
with open(out, "w", encoding="utf-8") as fh:
    for r in st.day:
        fh.write(f"{r['time']}\t{r['change']}\t{r['vol']}\t{r['price']}\t"
                 f"{r['name']}\t[{r['status']}]\n")
print(f"day -> {out}")