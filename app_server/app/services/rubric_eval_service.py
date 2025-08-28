# app/services/rubric_eval_service.py
# Bewertungsfragen zu einer Rubrik beantworten (Ports: retrieval_fn, ollama_url)
import os, json, urllib.request
from typing import Dict, Any, Callable
from app.services.rubrics_facade import get_rubric_by_id
from app.services.rubric_examples_facade import list_examples
from app.modules.prompt_builder import build_prompt
from app.modules.llm_router import resolve_model
from app.modules.llm_client import OllamaClient  # nutzt zentrale HTTP-Logik zu Ollama

def _read_app_cfg():
    path = os.getenv("APP_CONFIG_PATH", "/data/config/app_config.json")
    if os.path.exists(path):
        with open(path,"r",encoding="utf-8") as f: return json.load(f)
    return {"ollama_url":"http://host.docker.internal:11434"}

def _ollama_chat(ollama_url, model, system_prompt, user_prompt, options):
    """
    Robuster Ollama-Chat-Aufruf mit vereinheitlichter Rückgabe:
      -> { ok: bool, answer: str, raw: {...} }

    - 'ollama_url' darf None sein: Fallback auf Env/Default.
    - 'model' kann String ODER Dict sein (nimmt 'model' oder ersatzweise 'alias').
    - 'options' darf None sein.
    """
    # 1) Basis-URL robust bestimmen (nie None/leer)
    base = (
        (ollama_url or "").strip()
        or os.getenv("OLLAMA_BASE_URL", "").strip()
        or "http://host.docker.internal:11434"
    ).rstrip("/")

    # 2) Modellname extrahieren
    if isinstance(model, dict):
        model_name = (model.get("model") or model.get("alias") or "").strip()
    else:
        model_name = (model or "").strip()
    if not model_name:
        return {"ok": False, "answer": "", "raw": {"error": "invalid model name"}}

    # 3) Nachrichten & Optionen vorbereiten
    msgs = [
        {"role": "system", "content": system_prompt or ""},
        {"role": "user",   "content": user_prompt or ""},
    ]
    opts = options or {}

    # 4) Aufruf via zentralem Client
    client = OllamaClient(base)
    raw = client.chat(model=model_name, messages=msgs, options=opts)

    # 5) Ergebnis vereinheitlichen (answer = response)
    answer = raw.get("response", "")
    ok = bool(raw.get("ok", True if answer is not None else False))
    return {"ok": ok, "answer": answer, "raw": raw}


def evaluate_rubric_question(inp: Dict[str, Any], retrieval_fn: Callable[[Dict[str,Any]], Dict[str,Any]]=None) -> Dict[str, Any]:
    """
    inp: {rubric_id, question, doc_id(optional), subcategory_id(optional), top_k(optional)}
    retrieval_fn: callable that accepts {'query','doc_id','top_k'} -> {'context': str, 'chunks': [...]}
    """
    rubric_id = inp.get("rubric_id")
    sub_id = inp.get("subcategory_id")
    q = inp.get("question","")
    doc_id = inp.get("doc_id")
    top_k = inp.get("top_k")

    rub = get_rubric_by_id(rubric_id).get("rubric")
    if not rub: return {"ok": False, "error":"rubric_not_found"}
    node = rub
    if sub_id:
        for c in rub.get("children",[]) or []:
            if c.get("id")==sub_id: node=c; break

    ex = list_examples(rubric_id, sub_id).get("examples", [])

    ctx=""
    if retrieval_fn:
        ctx = retrieval_fn({"query": q or node.get("description",""),
                            "doc_id": doc_id, "top_k": top_k or node.get("top_k")}).get("context","")

    prompt = build_prompt({"rubric": node, "question": q, "context": ctx, "examples": ex})

    model = resolve_model(node.get("llm_alias")).get("model")
    ollama_url = _read_app_cfg().get("ollama_url")
    res = _ollama_chat(ollama_url, model, prompt["system"], prompt["user"], {})
    return {"ok": True, "answer": res["answer"],
            "used":{"rubric": node.get("id"), "doc_id": doc_id, "top_k": top_k or node.get("top_k")}}
