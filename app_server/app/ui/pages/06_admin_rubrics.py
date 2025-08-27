# app/ui/pages/06_admin_rubrics.py
# Streamlit-Adminseite für Rubriken & Beispiele – erweitert um Header/State (Doc-ID Vorbelegung)
import os, streamlit as st
from app.services.config_facade import ConfigFacade
from app.modules.logging_setup import setup_logging
from app.ui.components.theme import apply_css_only
from app.ui.components.topbar import render_topbar
from app.services.state_facade import StateFacade
from app.services.rubrics_facade import list_rubrics, upsert_rubric, upsert_subcategory, set_params, delete_node
from app.services.rubric_examples_facade import list_examples, add_example, delete_example

CFG_DIR = os.environ.get("ARANDU_CFG_DIR", "data/config")
cfg = ConfigFacade(CFG_DIR).load_app_config()
setup_logging(cfg["paths"])
apply_css_only(cfg)
render_topbar(cfg)

st.title("Rubriken verwalten")
data = list_rubrics(); rubrics = data.get("rubrics", []); defaults = data.get("defaults", {})

# Aktuelle Arbeit lesen, um Doc-ID als Default zu setzen
state = StateFacade(cfg["paths"]["app_state_dir"])
current = state.get_current() or {}
current_docid = (current.get("docid") or (current.get("metadata") or {}).get("docid") or "").strip()

with st.sidebar:
    st.header("Rubrik auswählen")
    sel = st.selectbox("Rubrik", ["<neu>"] + [r["id"] for r in rubrics])
    if sel == "<neu>":
        with st.form("new_rubric"):
            rid = st.text_input("Neue Rubrik-ID"); name = st.text_input("Name")
            desc = st.text_area("Beschreibung")
            llm = st.text_input("LLM-Alias", defaults.get("llm_alias",""))
            topk = st.number_input("Top-K", 1, 50, value=int(defaults.get("top_k",5)))
            if st.form_submit_button("Anlegen"):
                upsert_rubric({"id": rid, "name": name, "description": desc, "llm_alias": llm, "top_k": int(topk)})
                st.success("Rubrik angelegt.")

if sel and sel != "<neu>":
    r = next((r for r in rubrics if r.get("id")==sel), {})
    st.subheader(f"Rubrik: {r.get('name','')} ({r.get('id')})")
    llm = st.text_input("LLM-Alias", r.get("llm_alias",""))
    topk = st.number_input("Top-K", 1, 50, value=int(r.get("top_k",5)))
    c1, c2 = st.columns(2)
    if c1.button("Speichern (Rubrik)"):
        set_params(sel, {"llm_alias": llm, "top_k": int(topk)}); st.success("Gespeichert.")
    if c2.button("Rubrik löschen"):
        delete_node(sel); st.warning("Gelöscht – Seite neu laden.")

    st.markdown("### Unterkategorien")
    with st.form("add_sub"):
        sid = st.text_input("Sub-ID"); sname = st.text_input("Sub-Name")
        sdesc = st.text_area("Sub-Beschreibung")
        if st.form_submit_button("Hinzufügen"):
            upsert_subcategory(sel, {"id": sid, "name": sname, "description": sdesc}); st.success("Subkategorie gespeichert.")
    for c in (r.get("children") or []):
        st.caption(f"- {c.get('id')}: {c.get('name')}")

    st.markdown("### Beispiele")
    with st.form("add_example"):
        label = st.selectbox("Label", ["positive","negative"])
        etext = st.text_area("Beispieltext (Zitat/Auszug)")
        docid = st.text_input("Doc-ID (optional; vorbelegt)", value=current_docid)
        chunkid = st.text_input("Chunk-ID (optional)")
        if st.form_submit_button("Beispiel hinzufügen"):
            add_example({"rubric_id": sel, "subcategory_id": None, "label": label,
                         "text": etext, "source":{"doc_id":docid,"chunk_id":chunkid}})
            st.success("Beispiel gespeichert.")
    for e in list_examples(sel).get("examples", []):
        with st.expander(f"{e['id']} · {e['label']}"):
            st.write((e.get("text","") or "")[:800])
            if st.button(f"Beispiel löschen · {e['id']}"):
                delete_example(e["id"]); st.warning("Gelöscht.")
