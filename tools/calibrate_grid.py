import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import matplotlib; matplotlib.use("TkAgg")
import matplotlib.pyplot as plt, matplotlib.image as mpimg, numpy as np
import config

IMG_PATH = str(config.FIXTURES_DIR / "clean.png")   # a rescued complete frame

COL_X, ROW_TOP, ROW_H, N_ROWS = list(config.COL_X), config.ROW_TOP, config.ROW_H, config.N_ROWS
img = mpimg.imread(IMG_PATH); H, W = img.shape[:2]
fig, ax = plt.subplots(figsize=(7, 10)); ax.imshow(img)
ax.set_title("Drag RED=cols, drag BLUE=row grid up/down. "
             "[ ] row height | n m rows | p PRINT | q quit")
vlines = [ax.axvline(x=x, color="red", lw=1.2) for x in COL_X]
S = {"drag": None, "top": ROW_TOP, "h": ROW_H, "n": N_ROWS, "drag_row": False, "anchor": None}
hlines = [ax.axhline(y=S["top"]+i*S["h"], color="blue", lw=0.8) for i in range(S["n"]+1)]

def redraw():
    ys = [S["top"]+i*S["h"] for i in range(S["n"]+1)]
    while len(hlines) < len(ys): hlines.append(ax.axhline(y=0, color="blue", lw=0.8))
    for i, hl in enumerate(hlines):
        hl.set_visible(i < len(ys))
        if i < len(ys): hl.set_ydata([ys[i], ys[i]])
    fig.canvas.draw_idle()

def press(e):
    if e.inaxes != ax or e.xdata is None: return
    xs = [v.get_xdata()[0] for v in vlines]
    d = int(np.argmin([abs(e.xdata-x) for x in xs]))
    if abs(e.xdata-xs[d]) < 8: S["drag"] = d
    else: S["drag_row"], S["anchor"] = True, (e.ydata, S["top"])

def motion(e):
    if e.inaxes != ax or e.xdata is None: return
    if S["drag"] is not None:
        vlines[S["drag"]].set_xdata([e.xdata, e.xdata]); fig.canvas.draw_idle()
    elif S["drag_row"]:
        y0, t0 = S["anchor"]; S["top"] = t0 + (e.ydata - y0); redraw()

def release(e): S["drag"], S["drag_row"] = None, False

def key(e):
    if e.key == "]": S["h"] += 0.5; redraw()
    elif e.key == "[": S["h"] = max(1, S["h"]-0.5); redraw()
    elif e.key == "m": S["n"] += 1; redraw()
    elif e.key == "n": S["n"] = max(1, S["n"]-1); redraw()
    elif e.key == "p":
        xs = sorted(int(round(v.get_xdata()[0])) for v in vlines)
        print("\nCOL_X   =", xs)
        print("ROW_TOP =", int(round(S["top"])))
        print("ROW_H   =", round(S["h"], 1))
        print("N_ROWS  =", S["n"], "\n")
    elif e.key == "q": plt.close(fig)

for ev, fn in [("button_press_event", press), ("motion_notify_event", motion),
               ("button_release_event", release), ("key_press_event", key)]:
    fig.canvas.mpl_connect(ev, fn)
redraw(); plt.tight_layout(); plt.show()