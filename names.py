"""Company-name matching: messy Arabic OCR -> canonical EGX name.
Loads the 266-name canonical list (app's exact spellings) from the xlsx,
normalizes, and fuzzy-matches with rapidfuzz WRatio. Below CONFIDENCE_MIN
the row is flagged rather than trusted."""
import pandas as pd
from rapidfuzz import process, fuzz
import config

CONFIDENCE_MIN = 80          # scores below this => flag, don't trust

def _normalize(s):
    s = str(s).strip()
    # unify Arabic letter variants OCR & humans spell inconsistently
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    s = s.replace("ى", "ي").replace("ة", "ه")
    s = " ".join(s.split())   # collapse whitespace
    return s

# ---- load canonical list once ----
def _load_canonical():
    df = pd.read_excel(config.NAMES_XLSX, sheet_name=config.NAMES_SHEET, header=0)
    raw = df[df.columns[0]].dropna().astype(str).str.strip()
    raw = [r for r in raw if r]
    # map normalized form -> original canonical spelling
    return {_normalize(r): r for r in raw}

_canon_map = None
_canon_keys = None

def _canon():
    global _canon_map, _canon_keys
    if _canon_map is None:
        _canon_map = _load_canonical()
        _canon_keys = list(_canon_map.keys())
    return _canon_map, _canon_keys

def match_name(ocr_text):
    """Return (canonical_name, score, ok). ok=False => flag/reject the row."""
    text = _normalize(ocr_text)
    if not text.strip():                    # empty (incl. after time-strip) => flag
        return (None, 0.0, False)
    cmap, keys = _canon()
    key, score, _ = process.extractOne(text, keys, scorer=fuzz.WRatio)
    ok = score >= CONFIDENCE_MIN
    return (cmap[key], float(score), ok)