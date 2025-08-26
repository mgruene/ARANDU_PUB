# app/ui/pages/02_select_thesis.py
# Seite 02 · Arbeit auswählen + Metadaten/Diagnose anzeigen (Receipt-Fallback)
import os, json
import streamlit as st

from app.services.config_facade import ConfigFacade
from app.services.state_facade import StateFacade
from app.modules.logging_setup import setup_logging, get_logger
from app.ui.components.theme import apply_css_only
from app.ui.components.topbar import render_topbar
from app.modules.chroma_client import ChromaWrapper

log = get_logger("ui.select_thesis")

# --- Setup ---
CFG_DIR = os.environ.get("ARANDU_CFG_DIR", "data/config")
cfg = ConfigFacade(CFG_DIR).load_app_config()
setup_logging(cfg["paths"])
apply_css_only(cfg)
render_topbar(cfg)

st.title("Arbeit auswählen")

state = StateFacade(cfg["paths"]["app_state_dir"])
index = state.list_index() or []
current = state.get_current() or {}

def _read_receipt(docid: str) -> dict:
    """Bevorzugt state.read_receipt, fallback auf Datei."""
    try:
        if hasattr(state, "read_receipt"):
            return state.read_receipt(docid) or {}
    except Exception:
        pass
    p = os.path.join(cfg["paths"]["app_state_dir"], f"ingest_doc_{docid}.json")
    try:
        with open(p, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}

def _safe_rerun():
    """Kompatibel zu neuen/alten Streamlit-Versionen."""
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

# --- Aktuelle Arbeit + Receipt laden ---
cur_docid = (current.get("docid") or "").strip()
cur_rec = _read_receipt(cur_docid) if cur_docid else {}
cur_md = (cur_rec.get("metadata") or current.get("metadata") or {}) if cur_docid else {}
cur_title = cur_md.get("thesis_title") or "–"
cur_student = cur_md.get("student_name") or "–"

st.markdown(f"**Aktuelle Arbeit:** `{cur_docid or '–'}`  \n**Studierende/r:** {cur_student}  \n**Titel:** {cur_title}")

# --- Liste aller Arbeiten (Zeilen befüllen via Receipt-Fallback) ---
st.subheader("Vorhandene Arbeiten")
if not index:
    st.info("Keine Arbeiten vorhanden. Bitte zuerst ingestieren.")
else:
    for row in index:
        r_docid = (row.get("docid") or "").strip()
        r_rec = _read_receipt(r_docid) if r_docid else {}
        r_md = r_rec.get("metadata") or row.get("metadata") or {}
        r_title = r_md.get("thesis_title") or "–"
        r_student = r_md.get("student_name") or "–"

        c1, c2 = st.columns([0.75, 0.25])
        with c1:
            st.markdown(f"**{r_title}**  \n_{r_student}_  \n`{r_docid}`")
        with c2:
            if st.button("Arbeit auswählen", key=f"select_{r_docid}"):
                try:
                    state.set_current(r_docid)
                    st.success(f"Aktuelle Arbeit gesetzt: {r_docid}")
                    _safe_rerun()
                except Exception as e:
                    st.error(f"Konnte Arbeit nicht setzen: {e}")

st.divider()

# --- Metadatenblöcke (Fachlich + Tech aus Receipt) ---
st.subheader("Metadaten der ausgewählten Arbeit")
cols = (cur_rec.get("collections") or current.get("collections") or {})
counts = (cur_rec.get("counts") or current.get("counts") or {})
tech = {
    "embedding_alias": cur_rec.get("embedding_alias"),
    "embedding_model": cur_rec.get("embedding_model"),
    "embedding_dim": cur_rec.get("embedding_dim"),
    "embedding_normalize": cur_rec.get("embedding_normalize"),
    "collections": cols,
    "counts": counts,
    "ingest_at": cur_rec.get("ingest_at"),
}

with st.expander("Fachliche Metadaten", expanded=True):
    st.json(cur_md or {})

with st.expander("Technische Metadaten (Receipt)", expanded=True):
    st.json(tech)

# --- Chroma-Diagnose (Parents) ---
st.subheader("Chroma-Diagnose (aktuelle Arbeit)")
parents_col = (cols.get("parents") or "").strip()
if not parents_col:
    st.info("Keine Parents-Collection im Receipt gefunden. Bitte Arbeit ggf. neu ingestieren.")
else:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("**Parents-Collection:**")
        st.code(parents_col or "–")
    with c2:
        st.write("**DocID-Filter:**")
        st.code(cur_docid or "–")
    with c3:
        btn_check = st.button("1 Chunk-Metadaten prüfen", key="btn_check_chunk", use_container_width=True)

    if btn_check:
        try:
            chroma = ChromaWrapper(cfg.get("chroma") or {})
            col = chroma.get_or_create_collection(parents_col)
            # Count
            try:
                total = col.count()
                err_cnt = None
            except Exception as e_cnt:
                total, err_cnt = None, str(e_cnt)

            # Probe mit docid
            sample = {}
            try:
                got = col.get(where={"docid": cur_docid}, limit=1)
                docs = got.get("documents") or []
                metas = got.get("metadatas") or []
                if docs and isinstance(docs[0], list): docs = docs[0]
                if metas and isinstance(metas[0], list): metas = metas[0]
                sample = {
                    "documents_len": len(docs),
                    "meta_keys": list(metas[0].keys()) if metas else [],
                    "meta_preview": metas[0] if metas else {},
                }
                if not docs:
                    got2 = col.get(where={"doc_id": cur_docid}, limit=1)
                    d2 = got2.get("documents") or []
                    m2 = got2.get("metadatas") or []
                    if d2 and isinstance(d2[0], list): d2 = d2[0]
                    if m2 and isinstance(m2[0], list): m2 = m2[0]
                    sample.update({
                        "alt_key_doc_id_documents_len": len(d2),
                        "alt_key_meta_keys": list(m2[0].keys()) if m2 else [],
                        "alt_key_meta_preview": m2[0] if m2 else {},
                    })
            except Exception as e_get:
                sample = {"error": str(e_get)}

            st.markdown("**Collection-Status**")
            st.json({"count": total, "count_error": err_cnt})

            st.markdown("**Chunk-Metadaten (Probe)**")
            st.json(sample)

            st.info("Erwartet u. a.: `docid`, `embedding_alias`, `embedding_model`, `embedding_dim`, `embedding_normalize` "
                    "sowie fachliche Felder (z. B. `student_name`, `thesis_title`).")
        except Exception as e:
            st.error(f"Diagnose fehlgeschlagen: {e}")
