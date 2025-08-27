# app/services/rubric_examples_facade.py
# Verwaltung von Bewertungsbeispielen (positiv/negativ), file-basiert unter /data
import os, json, uuid, logging, datetime as dt
from typing import Dict, Any

EX_PATH = os.getenv("RUBRIC_EXAMPLES_PATH", "/data/config/rubric_examples.json")
LOG_PATH = os.getenv("APP_LOG_PATH", "/data/logs/app.log")

def _get_logger():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logging.basicConfig(filename=LOG_PATH, level=logging.INFO,
                        format="%(asctime)s %(levelname)s rubric_examples_facade %(message)s")
    return logging.getLogger("rubric_examples_facade")

log = _get_logger()

def _read() -> Dict[str, Any]:
    if not os.path.exists(EX_PATH):
        os.makedirs(os.path.dirname(EX_PATH), exist_ok=True)
        data = {"version":1,"updated_at":dt.datetime.utcnow().isoformat()+"Z","examples":[]}
        with open(EX_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data
    with open(EX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _write(data: Dict[str, Any]) -> Dict[str, Any]:
    data["updated_at"] = dt.datetime.utcnow().isoformat()+"Z"
    with open(EX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info(json.dumps({"event":"rubric_examples_saved","path":EX_PATH}))
    return {"ok": True, "path": EX_PATH}

def list_examples(rubric_id: str=None, subcat_id: str=None, label: str=None) -> Dict[str, Any]:
    data=_read(); ex=data.get("examples", [])
    def ok(e):
        return (rubric_id is None or e.get("rubric_id")==rubric_id) and \
               (subcat_id is None or e.get("subcategory_id")==subcat_id) and \
               (label is None or e.get("label")==label)
    return {"examples":[e for e in ex if ok(e)]}

def add_example(e: Dict[str, Any]) -> Dict[str, Any]:
    assert e.get("label") in ("positive","negative")
    e.setdefault("id", str(uuid.uuid4()))
    e.setdefault("created_at", dt.datetime.utcnow().isoformat()+"Z")
    data=_read()
    data["examples"].append(e)
    return _write(data)

def delete_example(example_id: str) -> Dict[str, Any]:
    data=_read()
    data["examples"] = [e for e in data.get("examples", []) if e.get("id")!=example_id]
    return _write(data)
