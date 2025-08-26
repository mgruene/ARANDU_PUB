# modules/ingest/metadata_ops.py
# ÄNDERUNGEN:
# - flatten_final_metadata: defensiv gegenüber None/Non-Dict; liefert immer (dict, dict, str)
# - klarere Typ-Guards

from typing import Dict, Any, Tuple, List
import json, math
from modules.logging_setup import get_logger

log = get_logger("ingest.metadata_ops")

REQUIRED = [
    "student_name","thesis_title","matriculation_number","study_program",
    "examiner_first","examiner_second","submission_date","work_type"
]
_PRIMITIVE = (str, int, float, bool)

def validate_required(md: Dict[str, Any]) -> List[str]:
    return [k for k in REQUIRED if not md.get(k)]

def _bad_float(x: Any) -> bool:
    return isinstance(x, float) and (math.isnan(x) or math.isinf(x))

def sanitize_value(v: Any) -> Any:
    """Chroma 0.6.x: nur str|int|float|bool; alles andere -> JSON-String; None/NaN/Inf -> None (drop)."""
    if v is None: return None
    if isinstance(v, _PRIMITIVE):
        if _bad_float(v): return None
        return v
    try: return json.dumps(v, ensure_ascii=False)
    except Exception: return str(v)

def sanitize_metadata(md: Dict[str, Any], context: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    dropped = {}
    for k, v in (md or {}).items():
        sv = sanitize_value(v)
        if sv is None:
            dropped[str(k)] = "None/NaN/Inf"
            continue
        out[str(k)] = sv
    if dropped:
        log.warning("metadata_sanitized_drop", extra={"extra_fields": {"context": context, "dropped": dropped}})
    log.debug("metadata_sanitized_sample", extra={"extra_fields": {"context": context, "keys": list(out.keys())[:10]}})
    return out

def flatten_final_metadata(meta_in: Any) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    """
    Outer > Inner. Zieht finale, flache Metadaten; gibt optional confidence/source separat zurück.
    Defensiv: akzeptiert None oder non-dict und behandelt sie als {}.
    """
    if not isinstance(meta_in, dict):
        meta_in = {}

    inner = meta_in.get("metadata") if isinstance(meta_in.get("metadata"), dict) else {}
    source = meta_in.get("source") or meta_in.get("metadata_source") or ""
    confidence = meta_in.get("confidence") if isinstance(meta_in.get("confidence"), dict) else {}

    keys = set(REQUIRED) | set(k for k in meta_in.keys() if k not in ["metadata","confidence","source","metadata_source"])
    final: Dict[str, Any] = {}
    for k in keys:
        ov = meta_in.get(k); iv = inner.get(k) if inner else None
        final[k] = ov if (ov not in [None,""]) else iv
    for k,v in (inner or {}).items():
        if k not in final or final[k] in [None,""]:
            final[k] = v
    for k,v in list(final.items()):
        if isinstance(v, str):
            final[k] = v.strip()

    return final, confidence, source
