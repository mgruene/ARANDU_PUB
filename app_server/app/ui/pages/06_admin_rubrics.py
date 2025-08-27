# app/ui/pages/06_admin_rubrics.py
# Streamlit-Adminseite für Rubriken & Beispiele (neu)
import streamlit as st
from app.services.rubrics_facade import list_rubrics, upsert_rubric, upsert_subcategory, set_params, delete_node
from app.services.rubric_examples_facade import list_examples, add_example, delete_example

st.set_page_config(page_title="Rubriken-Admin", layout="wide")
st.title("Rubriken verwalten")

data = list_rubrics()
rubrics = data.get("rubrics", [])
defaults = data.get("defaults", {})

with st.sidebar:
    st.header("Rubrik auswählen")
    rub_ids = ["<neu>"] + [r["id"] for r in rubrics]
    sel = st.selectbox("Rubrik", rub_ids)
    if sel=="<neu>":
        with st.form("new_rubric"):
            rid = st.text_input("ID", "content")
            name = st.text_input("Name", "Inhalt")
            desc = st.text_area("Beschreibung")
            llm = st.text_input("LLM-Alias", defaults.get("llm_alias",""))
            topk = st.number_input("Top-K", 1, 50, value=defaults.get("top_k",5))
            if st.form_submit_button("Anlegen"):
                upsert_rubric({"id": rid, "name": name, "description": desc, "llm_alias": llm, "top_k": int(topk)})
                st.success("Rubrik angelegt. Seite neu laden.")
    else:
        r = next(r for r in rubrics if r["id"]==sel)
        st.write(f"**{r['name']}**")
        llm = st.text_input("LLM-Alias", r.get("llm_alias",""))
        topk = st.number_input("Top-K", 1, 50, value=int(r.get("top_k",5)))
        if st.button("Speichern (Rubrik)"):
            set_params(sel, {"llm_alias": llm, "top_k": int(topk)})
            st.success("Gespeichert.")
        if st.button("Rubrik löschen"):
            delete_node(sel); st.warning("Gelöscht. Seite neu laden.")

if sel!="<neu>":
    r = next(r for r in rubrics if r["id"]==sel)
    st.subheader("Unterkategorien")
    with st.form("add_sub"):
        sid = st.text_input("Sub-ID", "")
        sname = st.text_input("Sub-Name", "")
        sdesc = st.text_area("Sub-Beschreibung", "")
        sllm = st.text_input("Sub-LLM-Alias (optional)", "")
        stopk = st.number_input("Sub-Top-K", 1, 50, value=int(r.get("top_k",5)))
        if st.form_submit_button("Subkategorie hinzufügen"):
            upsert_subcategory(sel, {"id": sid, "name": sname, "description": sdesc,
                                     "llm_alias": sllm or r.get("llm_alias"),
                                     "top_k": int(stopk)})
            st.success("Subkategorie angelegt.")
    for c in r.get("children",[]) or []:
        with st.expander(f"{c['id']} · {c['name']}"):
            st.write(c.get("description",""))
            cllm = st.text_input(f"LLM-Alias · {c['id']}", c.get("llm_alias", r.get("llm_alias","")))
            ctopk = st.number_input(f"Top-K · {c['id']}", 1, 50, value=int(c.get("top_k", r.get("top_k",5))))
            if st.button(f"Speichern · {c['id']}"):
                set_params(c["id"], {"llm_alias": cllm, "top_k": int(ctopk)})
                st.success("Gespeichert.")
            if st.button(f"Löschen · {c['id']}"):
                delete_node(c["id"]); st.warning("Gelöscht.")

    st.subheader("Bewertungsbeispiele")
    label = st.selectbox("Label", ["positive","negative"])
    etext = st.text_area("Beispieltext (Zitat/Auszug)")
    docid = st.text_input("Doc-ID (optional)")
    chunkid = st.text_input("Chunk-ID (optional)")
    if st.button("Beispiel hinzufügen"):
        add_example({"rubric_id": sel, "subcategory_id": None, "label": label,
                     "text": etext, "source":{"doc_id":docid,"chunk_id":chunkid}})
        st.success("Beispiel gespeichert.")
    ex = list_examples(sel).get("examples",[])
    for e in ex:
        with st.expander(f"{e['id']} · {e['label']}"):
            st.write(e.get("text","")[:500])
            if st.button(f"Beispiel löschen · {e['id']}"):
                delete_example(e["id"]); st.warning("Gelöscht.")
