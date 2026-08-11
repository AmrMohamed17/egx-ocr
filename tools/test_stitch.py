import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from stitch import Stitcher, find_overlap

def R(change, vol, price, time, name, status="ok"):
    return {"change": change, "vol": vol, "price": price, "time": time,
            "name": name, "name_score": 100.0, "status": status}

# Frame 1: 6 trades, newest first (simulates the visible window).
f1 = [R("9.04","3",    "567.00","10:04:01","جلاكسو ولكام"),
      R("9.18","130",  "174.88","10:04:01","ايبيكو"),
      R("0.00","4,823","9.22",  "10:04:01","بايونيرز بروبرتيز"),
      R("-0.19","3,234","15.47", "10:04:01","بالم هيلز"),
      R("-5.76","30",  "168.21","10:04:01","فوديكو"),
      R("2.89","570",  "14.97", "10:04:00","ابن سينا فارما")]

# Frame 2: 2 NEW trades at top; the rest scrolled down (overlap = last 4 of f1).
# Make the top new row's name FLAGGED (None) — simulates a faint/unread name.
f2 = [R("1.29","431",  "2.35",  "10:04:02", None, status="flag"),   # كريستمارك, unread
      R("9.68","116",  "286.00","10:04:02","ايجيفرت"),
      R("9.04","3",    "567.00","10:04:01","جلاكسو ولكام"),
      R("9.18","130",  "174.88","10:04:01","ايبيكو"),
      R("0.00","4,823","9.22",  "10:04:01","بايونيرز بروبرتيز"),
      R("-0.19","3,234","15.47", "10:04:01","بالم هيلز")]

# Frame 3: 1 new trade; and the previously-flagged كريستمارك row now READS clean.
f3 = [R("1.04","274",  "68.70", "10:04:03","اسيك للتعدين"),
      R("1.29","431",  "2.35",  "10:04:02","كريستمارك"),          # now reads
      R("9.68","116",  "286.00","10:04:02","ايجيفرت"),
      R("9.04","3",    "567.00","10:04:01","جلاكسو ولكام"),
      R("9.18","130",  "174.88","10:04:01","ايبيكو")]

print("overlap f1->f2:", find_overlap(f1, f2))   # expect k=2
print("overlap f2->f3:", find_overlap(f2, f3))   # expect k=1

s = Stitcher(min_run=4)
s.add_frame(f1)
s.add_frame(f2)
s.add_frame(f3)

print(f"\nassembled {len(s.day)} trades (expect 9), broken={s.broken}")
print(f"{'chg':>6} | {'vol':>6} | {'time':>8} | name")
print("-"*50)
for r in s.day:
    print(f"{r['change']:>6} | {r['vol']:>6} | {r['time']} | {r['name']}  [{r['status']}]")