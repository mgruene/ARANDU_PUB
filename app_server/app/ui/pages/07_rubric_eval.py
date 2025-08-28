# app/ui/pages/07_rubric_eval.py
# -----------------------------------------------------------------------------
# ARANDU – Rubrikbasierte Fragen
# - Header analog ask_thesis (Kopf + ausklappbare Metadaten)
# - Keine "weiße Seite" mehr: alle riskanten Schritte lazy + try/except mit UI-Fehlerpanel
# - Korrekte Pfadauflösung: Facades via ARANDU_CFG_DIR-Key, Direktzugriffe via absolutem Pfad
# - Retrieval docid-gefiltert; EmbeddingsFactory erhält app_cfg
# -----------------------------------------------------------------------------

from __future__ import annotations
import os, json, traceback
from typing import Any, Dict, List, Optional
import streamlit as st

# ------------------------- Pfad-/UI-Helfer -------------------------

def _cfg_key() -> str:
    """Schlüssel/relativer Pfad für Facades (Repository hängt /data davor)."""
    return os.getenv("ARANDU_CFG_DIR", "config")

def _cfg_dir_abs() -> str:
    """Absoluter Pfad für Direktzugriffe (Registry/JSON)."""
    v = _cfg_key()
    if v.startswith("/"):
        return v
    for base in ("/code/data", "/data"):
        p = os.path.join(base, v)
        if os.path.isdir(p):
            return p
    return v  # nur sinnvoll, wenn wirklich relativ vorhanden

def _safe_error_panel(title: str, err: Exception) -> None:
    st.error(title)
    with st.expander("Details öffnen"):
        st.code("".join(traceback.format_exception(type(err), err, err.__traceback__)), language="text")

# ------------------------- Retrieval-Kapsel -------------------------

def _build_retrieval(app_cfg: Dict[str, Any], cfg_dir_abs: str):
    """Erzeugt eine Retrieval-Funktion, die docid-gefiltert gegen Chroma sucht."""
    try:
        # Lazy-Import, damit Importfehler im UI landen
        from app.modules.model_registry import ModelRegistry
        from app.modules.embeddings_factory import EmbeddingsFactory
        from app.modules.chroma_client import ChromaWrapper
    except Exception as e:
        raise RuntimeError(f"Module konnten nicht importiert werden: {e}")

    reg = ModelRegistry(cfg_dir_abs)
    retr = reg.get_retrieval_cfg()

    emb_alias = retr.get("embedding_alias_default") or ""
    emb = reg.embedding_by_alias(emb_alias) if emb_alias else None
    if not emb:
        aliases = reg.list_embedding_aliases()
        emb = reg.embedding_by_alias(aliases[0]) if aliases else None
    if not emb:
        raise RuntimeError("Kein Embedding-Modell konfiguriert (model_config.json).")

    # WICHTIG: EmbeddingsFactory braucht app_cfg (wegen ollama.base_url)
    factory = EmbeddingsFactory(app_cfg, emb)
    chroma = ChromaWrapper(app_cfg.get("chroma") or {})
    collection = chroma.get_or_create_collection(retr.get("default_collection") or "default")

    def _retrieval(payload: Dict[str, Any]) -> Dict[str, Any]:
        q = (payload.get("query") or "").strip()
        k = int(payload.get("top_k") or (retr.get("top_k_default") or 5))
        doc_id = payload.get("doc_id")
        if not q:
            return {"context": "", "metas": []}
        vec = factory.embed([q])[0]
        raw = collection.query(
            query_embeddings=[vec],
            n_results=k,
            where={"docid": doc_id} if doc_id else None
        )
        docs = (raw.get("documents") or [[]])[0]
        metas = (raw.get("metadatas") or [[]])[0]
        ctx = "\n\n".join(docs) if isinstance(docs, list) else (docs or "")
        max_chars = int(retr.get("max_context_chars") or 8000)
        if len(ctx) > max_chars:
            ctx = ctx[:max_chars]
        return {"context": ctx, "metas": metas}

    return _retrieval

# ------------------------- Seite -------------------------

def main() -> None:
    st.set_page_config(page_title="Rubrik-Fragen", layout="wide")

    # Theme / Topbar lazy import – wenn’s fehlt, weiter ohne, aber nicht weiß
    try:
        from app.ui.components.theme import apply_css_only
        from app.ui.components.topbar import render_topbar
    except Exception:
        apply_css_only = render_topbar = None

    CFG_KEY = _cfg_key()
    CFG_ABS = _cfg_dir_abs()

    # ConfigFacade & StateFacade lazy import (UI-Fehler statt Weißbild)
    try:
        from app.services.config_facade import ConfigFacade
        from app.services.state_facade import StateFacade
        from app.services.rubrics_facade import list_rubrics, get_rubric_by_id
        from app.services.rubric_eval_service import evaluate_rubric_question
    except Exception as e:
        st.title("Rubrikbasierte Fragen")
        _safe_error_panel("Fehler beim Import von Services/Facades.", e)
        return

    # App-Config laden (über Key, nicht absoluten Pfad)
    try:
        app_cfg = ConfigFacade(CFG_KEY).load_app_config()
    except Exception as e:
        st.title("Rubrikbasierte Fragen")
        _safe_error_panel("App-Konfiguration konnte nicht geladen werden.", e)
        return

    # Theme/Topbar (falls verfügbar) wie auf ask_thesis
    if apply_css_only:
        try:
            apply_css_only(app_cfg)
        except Exception as e:
            _safe_error_panel("CSS/Theme konnte nicht angewendet werden.", e)
    if render_topbar:
        try:
            render_topbar(app_cfg)
        except Exception as e:
            _safe_error_panel("Topbar konnte nicht gerendert werden.", e)

    st.title("Rubrikbasierte Fragen")

    # State laden + Header (analog ask_thesis: Kopf + Expander)
    try:
        state = StateFacade(app_cfg["paths"]["app_state_dir"])
        current = state.get_current() or {}
        md = current.get("metadata") or {}
        docid = (current.get("docid") or md.get("docid") or "").strip()
        student = md.get("student_name") or "–"
        title = md.get("thesis_title") or "–"
    except Exception as e:
        _safe_error_panel("App-State konnte nicht gelesen werden.", e)
        return

    st.markdown(f"**Studierende/r:** {student}  \n**Titel:** {title}")
    if not docid:
        st.info("Es ist keine Arbeit ausgewählt. Bitte zuerst unter **„Arbeit auswählen“** eine Arbeit setzen.")
        return

    with st.expander("Metadaten der Arbeit"):
        st.markdown(
            f"- docid: `{docid}`\n"
            f"- Arbeitstyp: {md.get('work_type','–')}\n"
            f"- Abgabedatum: {md.get('submission_date','–')}\n"
            f"- Erstprüfer/in: {md.get('examiner_first','–')}\n"
            f"- Zweitprüfer/in: {md.get('examiner_second','–')}\n"
            f"- Studiengang: {md.get('study_program','–')}\n"
        )

    # Rubriken laden
    try:
        rub_all = list_rubrics()
        rubrics = rub_all.get("rubrics", [])
        if not rubrics:
            st.info("Keine Rubriken vorhanden. Bitte zuerst unter **Rubriken verwalten** anlegen.")
            return
    except Exception as e:
        _safe_error_panel("Rubriken konnten nicht geladen werden.", e)
        return

    # UI – zentriert
    L, M, R = st.columns([1, 3, 1])
    with M:
        try:
            rid = st.selectbox("Rubrik", [r["id"] for r in rubrics])
            chosen = get_rubric_by_id(rid).get("rubric") or {}
            subs = [c.get("id") for c in (chosen.get("children") or []) if c.get("id")]
            sub_id = st.selectbox("Unterkategorie (optional)", ["<keine>"] + subs)
            question = st.text_area("Frage", placeholder="Was sagt die Arbeit zum Stand der Forschung in Bezug auf …?")

            # Default top_k: Rubrik → defaults → retrieval
            try:
                from app.modules.model_registry import ModelRegistry
                top_k_default = int(
                    (chosen.get("top_k")
                     or (rub_all.get("defaults") or {}).get("top_k")
                     or (ModelRegistry(CFG_ABS).get_retrieval_cfg().get("top_k_default") or 5))
                )
            except Exception:
                top_k_default = 5
            top_k = st.number_input("Top-K", min_value=1, max_value=50, value=top_k_default, step=1)

            # Retrieval vorbereiten
            try:
                retrieval_fn = _build_retrieval(app_cfg, CFG_ABS)
            except Exception as e:
                _safe_error_panel("Retrieval konnte nicht initialisiert werden.", e)
                return

            if st.button("Antwort generieren"):
                try:
                    req = {
                        "rubric_id": rid,
                        "subcategory_id": (None if sub_id == "<keine>" else sub_id),
                        "question": question,
                        "doc_id": docid,
                        "top_k": int(top_k),
                    }
                    res = evaluate_rubric_question(req, retrieval_fn=retrieval_fn)
                    if not res.get("ok"):
                        st.error(f"Fehler: {res.get('error')}")
                    else:
                        st.subheader("Antwort")
                        st.write(res.get("answer", ""))
                        st.caption(json.dumps(res.get("used", {})))
                except Exception as e:
                    _safe_error_panel("Fehler beim Generieren der Antwort.", e)
        except Exception as e:
            _safe_error_panel("Fehler in der UI-Interaktion.", e)

# Niemals "weiß": globaler Guard
try:
    main()
except Exception as _e:
    st.title("Rubrikbasierte Fragen")
    _safe_error_panel("Unerwarteter Fehler beim Rendern der Seite.", _e)
