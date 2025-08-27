# app/ui/pages/07_rubric_eval.py
import os, json, streamlit as st
from app.services.rubrics_facade import list_rubrics, get_rubric_by_id
from app.services.rubric_eval_service import evaluate_rubric_question

st.set_page_config(page_title="Rubrik-Fragen", layout="wide")
st.title("Fragen nach Bewertungskategorien")

data = list_rubrics()
rubrics = data.get("rubrics", [])
if not rubrics:
    st.warning("Keine Rubriken vorhanden. Bitte zuerst unter 'Rubriken-Admin' anlegen.")
    st.stop()

rid = st.selectbox("Rubrik", [r["id"] for r in rubrics])
sub = None
r = get_rubric_by_id(rid).get("rubric")
if r and r.get("children"):
    sub = st.selectbox("Unterkategorie", ["(keine)"]+[c["id"] for c in r["children"]])
    if sub=="(keine)": sub=None

# Doc-Auswahl
doc_id = ""
state_path = "/data/app_state/current_thesis.json"
if os.path.exists(state_path):
    with open(state_path,"r",encoding="utf-8") as f:
        cur = json.load(f); doc_id = cur.get("doc_id","")
doc_id = st.text_input("Doc-ID (leer = keine Filterung)", value=doc_id)

q = st.text_area("Frage/Auftrag", "Bewerte die Erfüllung des Kriteriums in der vorliegenden Arbeit.")
top_k = st.number_input("Top-K (Override, 0 = Rubrikwert nutzen)", 0, 50, 0)

# Retrieval-Port optional nutzen
try:
    from app.modules.retrieval_port import try_search as _retrieval
except Exception:
    def _retrieval(payload): return {"context": ""}

if st.button("Antwort generieren"):
    res = evaluate_rubric_question({
        "rubric_id": rid, "subcategory_id": sub, "question": q,
        "doc_id": doc_id, "top_k": int(top_k) or None
    }, retrieval_fn=_retrieval)
    if res.get("ok"):
        st.subheader("Antwort")
        st.write(res.get("answer",""))
        st.caption(json.dumps(res.get("used",{})))
    else:
        st.error(res.get("error","Unbekannter Fehler"))
