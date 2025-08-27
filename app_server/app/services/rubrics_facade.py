# app/services/rubrics_facade.py
# Fassade für Rubrikenverwaltung (neu; Pfade auf /data/ ausgerichtet)
import os, json, logging, datetime as dt
from typing import Dict, Any, List

CONFIG_PATH = os.getenv("RUBRICS_CONFIG_PATH", "/data/config/rubrics_config.json")
LOG_PATH = os.getenv("APP_LOG_PATH", "/data/logs/app.log")

def _get_logger():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logging.basicConfig(filename=LOG_PATH, level=logging.INFO,
                        format="%(asctime)s %(levelname)s rubrics_facade %(message)s")
    return logging.getLogger("rubrics_facade")

log = _get_logger()

def _read() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        cfg = {"version": 1, "updated_at": dt.datetime.utcnow().isoformat()+"Z",
               "rubrics": [], "defaults": {"llm_alias": "critique-llm", "top_k": 6, "max_context_chars": 8000}}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return cfg
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _write(cfg: Dict[str, Any]) -> Dict[str, Any]:
    cfg["updated_at"] = dt.datetime.utcnow().isoformat()+"Z"
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    log.info(json.dumps({"event":"rubrics_config_saved","path":CONFIG_PATH}))
    return {"ok": True, "path": CONFIG_PATH}

def list_rubrics() -> Dict[str, Any]:
    cfg = _read()
    return {"rubrics": cfg.get("rubrics", []), "defaults": cfg.get("defaults", {})}

def get_rubric_by_id(rubric_id: str) -> Dict[str, Any]:
    cfg = _read()
    for r in cfg.get("rubrics", []):
        if r.get("id")==rubric_id:
            return {"rubric": r}
    return {"rubric": None}

def _upsert(node_list: List[Dict[str,Any]], node: Dict[str,Any]) -> List[Dict[str,Any]]:
    hit=False
    for i, n in enumerate(node_list):
        if n.get("id")==node.get("id"):
            node_list[i] = node; hit=True; break
    if not hit: node_list.append(node)
    return node_list

def upsert_rubric(rubric: Dict[str, Any]) -> Dict[str, Any]:
    assert "id" in rubric and "name" in rubric
    cfg = _read()
    cfg["rubrics"] = _upsert(cfg.get("rubrics", []), rubric)
    return _write(cfg)

def upsert_subcategory(rubric_id: str, subcat: Dict[str, Any]) -> Dict[str, Any]:
    assert "id" in subcat and "name" in subcat
    cfg = _read()
    for r in cfg.get("rubrics", []):
        if r.get("id")==rubric_id:
            children = r.get("children", []) or []
            r["children"] = _upsert(children, subcat)
            return _write(cfg)
    return {"ok": False, "error": "rubric_not_found"}

def set_params(node_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _read()
    def patch(n):
        if n.get("id")==node_id:
            n.update({k:v for k,v in params.items() if v is not None})
            return True
        for c in n.get("children", []) or []:
            if patch(c): return True
        return False
    changed=False
    for r in cfg.get("rubrics", []):
        if patch(r): changed=True; break
    if not changed: return {"ok": False, "error":"node_not_found"}
    return _write(cfg)

def delete_node(node_id: str) -> Dict[str, Any]:
    cfg = _read()
    def drop(lst):
        return [n for n in lst if n.get("id")!=node_id]
    for r in cfg.get("rubrics", []):
        r["children"] = drop(r.get("children", []))
    cfg["rubrics"] = drop(cfg.get("rubrics", []))
    return _write(cfg)
