"""Stitcher: assemble a stream of read_frame() outputs into one ordered,
de-duplicated day. New trades push in at the TOP; older ones scroll down.
Consecutive frames overlap (guaranteed by capture rate), so each new frame is
[new rows] + [rows shared with previous frame]. We locate the shared run (the
anchor) and append only the rows above it. We NEVER dedup by content — genuine
duplicate trades exist — only by scroll position via the anchor."""

def _key(row):
    """Stable identity of a trade across frames: the numeric fields, which read
    consistently. Name is excluded (it flags inconsistently and gets voted in
    separately). Returns None for empty rows (no trade)."""
    if row["status"] == "empty":
        return None
    return (row["change"], row["vol"], row["price"], row["time"])

def _data_rows(frame):
    """Frame rows that hold a trade (drop trailing empties below the last trade)."""
    return [r for r in frame if r["status"] != "empty"]

def find_overlap(prev_rows, new_rows, min_run=4):
    """Return the index in new_rows where prev_rows' content begins (the anchor),
    i.e. how many rows at the top of new_rows are NEW.

    Strategy: the top of prev_rows should reappear somewhere in new_rows, shifted
    down by however many new rows arrived. We search for the offset `k` such that
    new_rows[k], new_rows[k+1], ... match prev_rows[0], prev_rows[1], ... for a
    run of at least min_run rows. The smallest such k is the count of new rows.

    Returns (k, run_len). If no run of >= min_run is found, returns (None, 0)
    -> overlap broken (too many new rows arrived; a burst outran the window).
    """
    pk = [_key(r) for r in prev_rows]
    nk = [_key(r) for r in new_rows]

    best = (None, 0)
    # try each possible offset: prev's top aligns at new_rows[k]
    for k in range(len(nk)):
        run = 0
        while (k + run < len(nk) and run < len(pk)
               and nk[k + run] is not None
               and nk[k + run] == pk[run]):
            run += 1
        if run >= min_run:
            return (k, run)        # smallest k with a valid run = the anchor
        if run > best[1]:
            best = (k, run)
    return (None, best[1])          # no valid run -> overlap broken


class Stitcher:
    """Feeds frames in order, maintains the assembled day (newest-first list of
    trade rows). Also votes across frames to fill flagged fields."""

    def __init__(self, min_run=4):
        self.day = []          # assembled trades, newest first
        self.min_run = min_run
        self.prev = None       # previous frame's data rows
        self.broken = 0        # count of overlap-break events (diagnostics)

    def add_frame(self, frame):
        rows = _data_rows(frame)
        if not rows:
            return
        if self.prev is None:
            # first frame: the whole visible window is our starting content
            self.day = list(rows)
            self.prev = rows
            return

        k, run = find_overlap(self.prev, rows, self.min_run)
        if k is None:
            # overlap broke: we cannot safely align. Record it; append nothing
            # rather than guess (a burst outran the window — a capture-rate issue,
            # surfaced here for diagnosis, not silently mis-stitched).
            self.broken += 1
            self.prev = rows
            return

        # rows[0:k] are NEW (arrived since prev). Prepend them, newest first.
        new_trades = rows[0:k]
        self.day = new_trades + self.day

        # voting: rows[k:] overlap with prev — if a field flagged in one frame
        # but read in the other, fill it in.
        self._vote(rows)
        self.prev = rows

    def _vote(self, new_rows):
        """Where the new frame read a name that a matching already-stored row had
        flagged, fill it in (and vice versa). Matches on numeric key."""
        by_key = {}
        for r in self.day:
            kb = _key(r)
            if kb is not None:
                by_key.setdefault(kb, r)
        for r in new_rows:
            kb = _key(r)
            stored = by_key.get(kb)
            if stored is None:
                continue
            # fill a flagged/missing name from whichever frame has it
            if (stored.get("name") is None) and r.get("name") is not None:
                stored["name"] = r["name"]
                stored["name_score"] = r["name_score"]
                if stored["status"] == "flag":
                    stored["status"] = "ok"