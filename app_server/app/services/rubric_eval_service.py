# app/services/rubric_eval_service.py
# Bewertungsfragen zu einer Rubrik beantworten (Ports: retrieval_fn, ollama_url)
import os, json, urllib.request
from typing import Dict, Any, Callable
from app.services.rubrics_facade import get_rubric_by_id
from app.services.rubric_examples_facade import list_examples
from app.modules.prompt_builder import build_prompt
from app.modules.llm_router import resolve_model

def _read_app_cfg():
    path = os.getenv("APP_CONFIG_PATH", "/data/config/app_config.json")
    if os.path.exists(path):
        with open(path,"r",encoding="utf-8") as f: return json.load(f)
    return {"ollama_url":"http://host.docker.internal:11434"}

def _ollama_chat(ollama_url: str, model: str, system: str, user: str, params: Dict[str,Any]) -> Dict[str,Any]:
    url = ollama_url.rstrip("/") + "/api/chat"
    body = {"model": model, "messages":[{"role":"system","content":system},{"role":"user","content":user}], "options": params or {}}
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return {"answer": data.get("message",{}).get("content",""), "raw": data}

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
