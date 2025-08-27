# app/ui/pages/07_rubric_eval.py
# Rubrik-basierte Fragen – lädt Metadaten/Doc-ID aus State + Header/Topbar, docid-gefiltertes Retrieval
import os, json, streamlit as st
from app.services.config_facade import ConfigFacade
from app.modules.logging_setup import setup_logging
from app.ui.components.theme import apply_css_only
from app.ui.components.topbar import render_topbar
from app.services.state_facade import StateFacade
from app.services.rubrics_facade import list_rubrics, get_rubric_by_id
from app.services.rubric_eval_service import evaluate_rubric_question
from app.modules.embeddings_factory import EmbeddingsFactory
from app.modules.chroma_client import ChromaWrapper

CFG_DIR = os.environ.get("ARANDU_CFG_DIR", "data/config")
cfg = ConfigFacade(CFG_DIR).load_app_config()
setup_logging(cfg["paths"])
apply_css_only(cfg); render_topbar(cfg)

st.title("Fragen nach Bewertungskategorien")

data = list_rubrics(); rubrics = data.get("rubrics", [])
if not rubrics:
    st.warning("Keine Rubriken vorhanden. Bitte zuerst unter 'Rubriken-Admin' anlegen."); st.stop()

# Aktuelle Arbeit laden
state = StateFacade(cfg["paths"]["app_state_dir"])
current = state.get_current()
if not current:
    st.warning("Keine aktuelle Arbeit ausgewählt. Bitte zuerst unter 'Arbeit auswählen' setzen."); st.stop()
docid = (current.get("docid") or (current.get("metadata") or {}).get("docid") or "").strip()
st.caption(f"Aktuelle Doc-ID: `{docid}`")

rid = st.selectbox("Rubrik", [r["id"] for r in rubrics])
rub = get_rubric_by_id(rid).get("rubric") or {}
subs = [c.get("id") for c in (rub.get("children") or []) if c.get("id")]
sub = st.selectbox("Unterkategorie (optional)", ["<keine>"] + subs)
q = st.text_area("Frage", placeholder="Was sagt die Arbeit zum Stand der Forschung in Bezug auf …?")
top_k = st.number_input("Top-K (optional, überschreibt Rubrik-Default)", min_value=1, max_value=50, value=int(rub.get("top_k",5)))

def _retrieval(payload):
    """DocID-gefilterte Kontextsuche via Chroma; nutzt erstes Embedding aus model_config.json."""
    try:
        model_cfg = ConfigFacade(CFG_DIR).load_model_config()
        emb_list = model_cfg.get("embeddings") or []
        if not emb_list:
            return {"context": ""}
        emb_cfg = emb_list[0]
        vec = EmbeddingsFactory(cfg, emb_cfg).embed_robust([payload.get("query","").strip() or ""])[0]
        col = ChromaWrapper(cfg.get("chroma") or {}).get_or_create_collection((model_cfg.get("retrieval") or {}).get("default_collection","default"))
        raw = col.query(query_embeddings=[vec], n_results=int(payload.get("top_k") or 5), where={"docid": payload.get("doc_id")})
        docs = (raw.get("documents") or [[]])[0]
        ctx = "\n\n".join(docs) if isinstance(docs, list) else (docs or "")
        return {"context": ctx}
    except Exception:
        return {"context": ""}

if st.button("Antwort generieren"):
    res = evaluate_rubric_question({
        "rubric_id": rid, "subcategory_id": (None if sub=="<keine>" else sub),
        "question": q, "doc_id": docid, "top_k": int(top_k) or None
    }, retrieval_fn=_retrieval)
    if res.get("ok"):
        st.subheader("Antwort"); st.write(res.get("answer",""))
        st.caption(json.dumps(res.get("used",{})))
    else:
        st.error(res.get("error","Unbekannter Fehler"))
