# app/ui/components/metadata_editor.py
# Formular zur Prüfung/Anpassung der erkannten Metadaten.
# Gibt ein komplettes Dict (alle Pflichtfelder + zusätzliche Felder unverändert) zurück.

import streamlit as st
from typing import Dict, Any

REQUIRED_ORDER = [
    "student_name","thesis_title","matriculation_number","study_program",
    "examiner_first","examiner_second","submission_date","work_type"
]

def render_metadata_editor(md: Dict[str, Any]) -> Dict[str, Any]:
    st.subheader("Metadaten prüfen & ergänzen")

    # Vorbelegen der Pflichtfelder
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("Studierende*r", md.get("student_name",""))
        thesis_title = st.text_input("Titel der Arbeit", md.get("thesis_title",""))
        matric = st.text_input("Matrikelnummer", md.get("matriculation_number",""))
        study_program = st.text_input("Studiengang", md.get("study_program",""))
    with col2:
        examiner_first  = st.text_input("Erstprüfer*in", md.get("examiner_first",""))
        examiner_second = st.text_input("Zweitprüfer*in", md.get("examiner_second",""))
        submission_date = st.text_input("Abgabedatum (YYYY-MM-DD)", md.get("submission_date",""))
        work_type = st.selectbox("Arbeitstyp",
                                 options=["bachelor","master","seminararbeit","praxisarbeit","projektarbeit"],
                                 index=max(0, ["bachelor","master","seminararbeit","praxisarbeit","projektarbeit"].index(md.get("work_type","bachelor")) if md.get("work_type") in ["bachelor","master","seminararbeit","praxisarbeit","projektarbeit"] else 0))

    # Ergebnis-Metadaten zusammenbauen:
    out = dict(md)  # weitere (nicht-pflichtige) Felder beibehalten
    out.update({
        "student_name": student_name.strip(),
        "thesis_title": thesis_title.strip(),
        "matriculation_number": matric.strip(),
        "study_program": study_program.strip(),
        "examiner_first": examiner_first.strip(),
        "examiner_second": examiner_second.strip(),
        "submission_date": submission_date.strip(),
        "work_type": work_type,
    })

    # Optional: weitere Felder sichtbar machen
    with st.expander("Weitere erkannte Felder"):
        # Zeigt die restlichen Keys, sortiert, ohne die Pflichtfelder
        extra = {k: v for k, v in md.items() if k not in REQUIRED_ORDER}
        if extra:
            st.json(extra)
        else:
            st.caption("Keine weiteren Felder vorhanden.")

    return out
