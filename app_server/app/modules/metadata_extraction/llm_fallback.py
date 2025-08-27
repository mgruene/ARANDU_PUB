# app_server/app/modules/metadata_extraction/llm_fallback.py
# Robuster LLM-Fallback für Metadaten: arbeitet mit dem neuen OllamaClient (Dict-Response).
from __future__ import annotations
from typing import Dict, Any, List
import json, re

from app.modules.llm_client import OllamaClient  # nutzt vorhandenen HTTP-Client

def _pick_base_url(app_cfg: Dict[str, Any]) -> str | None:
    """Liest die Ollama-Base-URL aus app_cfg['ollama']['base_url'], falls vorhanden."""
    return ((app_cfg or {}).get("ollama") or {}).get("base_url")

def _coerce_response_to_text(resp: Any) -> str:
    """Akzeptiert Dict (neuer Client) oder String (alter Client) und liefert Text."""
    if isinstance(resp, dict):
        s = resp.get("response")
        if isinstance(s, str) and s.strip():
            return s
        raw = resp.get("raw")
        if isinstance(raw, dict):
            s2 = raw.get("response")
            if isinstance(s2, str):
                return s2
        # Fallback: zur Diagnose notfalls seriell darstellen
        try:
            return json.dumps(resp, ensure_ascii=False)
        except Exception:
            return str(resp)
    return "" if resp is None else str(resp)

def llm_fill_missing(
    first_page_text: str,
    missing_fields: List[str],
    llm_cfg: Dict[str, Any],
    app_cfg: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Ergänzt ausschließlich die fehlenden Felder per LLM.
    I/O deterministisch: nimmt Primitive/Dicts, gibt Dict[str,str] zurück.
    """
    # Nichts zu tun?
    wanted = [k for k in [
        "student_name","thesis_title","matriculation_number","study_program",
        "examiner_first","examiner_second","submission_date","work_type"
    ] if k in (missing_fields or [])]
    if not wanted:
        return {}

    base_url = _pick_base_url(app_cfg)
    client = OllamaClient(base_url)
    model = llm_cfg.get("model")
    options = llm_cfg.get("params") or {}

    # Schlanker System-Prompt: ausschließlich gewünschte Schlüssel im JSON ausgeben.
    sys_prompt = (
        "Extrahiere die folgenden Metadaten ausschließlich aus dem Text der Titelseite. "
        "Gib NUR kompaktes JSON ohne zusätzliche Erklärungen aus. "
        f"Schlüssel: {', '.join(wanted)}."
    )
    prompt = f"{sys_prompt}\n\nTEXT (unverändert):\n{first_page_text}"

    resp = client.generate(model=model, prompt=prompt, options=options)
    text = _coerce_response_to_text(resp)

    # JSON-Block herausziehen (robust gegen Prä-/Suffixe)
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return {}

    try:
        data = json.loads(m.group(0))
    except Exception:
        return {}

    # Nur die gewünschten Schlüssel als Strings zurückgeben
    out: Dict[str, Any] = {}
    for k in wanted:
        v = data.get(k)
        if v is None:
            continue
        out[k] = v if isinstance(v, str) else str(v)
    return out
