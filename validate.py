"""Validation: catch gross OCR misreads (out-of-range) before the day file.
In-range errors are caught by voting, not here. Never emit wrong undetected."""
import config

def _to_float(s):
    if s is None: return None
    try: return float(str(s).replace(",", ""))
    except ValueError: return None

def validate_row(row):
    """Return (ok, reasons). Does not mutate row."""
    reasons = []
    chg = _to_float(row.get("change"))
    if chg is None:                         reasons.append("change_unparseable")
    elif abs(chg) > config.CHANGE_LIMIT:    reasons.append(f"change_range({chg})")
    price = _to_float(row.get("price"))
    if price is None:                       reasons.append("price_unparseable")
    elif price <= 0:                        reasons.append("price_nonpositive")
    vol = _to_float(row.get("vol"))
    if vol is None:                         reasons.append("vol_unparseable")
    elif vol <= 0 or vol != int(vol):       reasons.append("vol_invalid")
    t = row.get("time")
    if not t or len(str(t)) != 8 or str(t)[2] != ":" or str(t)[5] != ":":
        reasons.append("time_malformed")
    if row.get("name") is None:             reasons.append("name_flagged")
    return (len(reasons) == 0, reasons)