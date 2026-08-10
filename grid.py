"""Cell geometry. Carries the fractional row height through and rounds
per-row, so error never accumulates down the table."""
import config

def row_bounds(i):
    top = int(round(config.ROW_TOP + i * config.ROW_H))
    bot = int(round(config.ROW_TOP + (i + 1) * config.ROW_H))
    return top, bot

def cell_crop(img, i, col):
    top, bot = row_bounds(i)
    x0, x1 = config.COL_X[col], config.COL_X[col + 1]
    return img[top:bot, x0:x1]