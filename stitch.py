"""Stitcher: assemble frames into one ordered de-duplicated day.
- add_frame():    full-read mode. Content-anchor + voting (repairs flagged rows).
- add_new_rows(): new-rows mode. Prepend already-read new rows (no voting).
Never dedup by content; only by scroll position via the anchor."""

def _key(row):
    if row is None or row["status"] == "empty": return None
    return (row["change"], row["vol"], row["price"], row["time"])

def _data_rows(frame):
    return [r for r in frame if r is not None and r["status"] != "empty"]

def find_overlap(prev_rows, new_rows, min_run=4):
    pk = [_key(r) for r in prev_rows]
    nk = [_key(r) for r in new_rows]
    best = (None, 0)
    for k in range(len(nk)):
        run = 0
        while (k + run < len(nk) and run < len(pk)
               and nk[k+run] is not None and nk[k+run] == pk[run]):
            run += 1
        if run >= min_run: return (k, run)
        if run > best[1]: best = (k, run)
    return (None, best[1])

class Stitcher:
    def __init__(self, min_run=4):
        self.day = []; self.min_run = min_run; self.prev = None; self.broken = 0

    def add_frame(self, frame):
        rows = _data_rows(frame)
        if not rows: return
        if self.prev is None:
            self.day = list(rows); self.prev = rows; return
        k, run = find_overlap(self.prev, rows, self.min_run)
        if k is None:
            self.broken += 1; self.prev = rows; return
        self.day = rows[0:k] + self.day
        self._vote(rows); self.prev = rows

    def add_new_rows(self, new_rows):
        clean = _data_rows(new_rows)
        self.day = clean + self.day

    def _vote(self, new_rows):
        by_key = {}
        for r in self.day:
            kb = _key(r)
            if kb is not None: by_key.setdefault(kb, r)
        for r in new_rows:
            stored = by_key.get(_key(r))
            if stored is None: continue
            if stored.get("name") is None and r.get("name") is not None:
                stored["name"] = r["name"]; stored["name_score"] = r["name_score"]
                if stored["status"] == "flag": stored["status"] = "ok"