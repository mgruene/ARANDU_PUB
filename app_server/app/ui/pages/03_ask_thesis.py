# app/ui/pages/03_ask_thesis.py
# Seite 03 · Frage an die Arbeit stellen (Kontext, Prompt & Parameter sichtbar)
import os
import streamlit as st

from app.services.config_facade import ConfigFacade
from app.services.state_facade import StateFacade
from app.modules.model_registry import ModelRegistry
from app.modules.logging_setup import setup_logging, get_logger
from app.ui.components.theme import apply_css_only
from app.ui.components.topbar import render_topbar
from app.modules.llm_client import OllamaClient
from app.modules.embeddings_factory import EmbeddingsFactory
from app.modules.chroma_client import ChromaWrapper

log = get_logger("ui.ask_thesis")

# ---- Setup / Konfig ----
CFG_DIR = os.environ.get("ARANDU_CFG_DIR", "data/config")
cfg = ConfigFacade(CFG_DIR).load_app_config()
setup_logging(cfg["paths"])
apply_css_only(cfg)
render_topbar(cfg)

st.title("Frage an die Arbeit stellen")

# ---- Aktuelle Arbeit laden ----
state = StateFacade(cfg["paths"]["app_state_dir"])
current = state.get_current() or {}
md = current.get("metadata") or {}
docid = (current.get("docid") or md.get("docid") or "").strip()
student = md.get("student_name") or "–"
title = md.get("thesis_title") or "–"
work_type = (md.get("work_type") or "default").strip().lower()
st.markdown(f"**Studierende/r:** {student}  \n**Titel:** {title}")
if not docid:
    st.info("Es ist keine Arbeit ausgewählt. Bitte zuerst unter **„Arbeit auswählen“** eine Arbeit setzen.")
    st.stop()

# ---- Modelle / Defaults ----
model_reg = ModelRegistry(cfg["paths"]["config_dir"])
model_cfg = getattr(model_reg, "_cfg", {}) or {}
llm_list = [m for m in model_cfg.get("llms", []) if (m.get("provider") or "").lower() == "ollama"]
if not llm_list:
    st.error("Keine Ollama LLMs in model_config.json gefunden."); st.stop()
retrieval_cfg = model_cfg.get("retrieval", {}) if isinstance(model_cfg, dict) else {}
top_k_default = int(retrieval_cfg.get("top_k_default", 5))
emb_alias = current.get("embedding_alias") or retrieval_cfg.get("embedding_alias_default") or retrieval_cfg.get("embedding_alias") or "default"
emb_cfg = next((e for e in model_cfg.get("embeddings", []) or [] if e.get("alias") == emb_alias), None)

# ---- UI: Auswahl ----
c1, c2 = st.columns([0.6, 0.4])
with c1:
    llm_aliases = [m.get("alias") or m.get("model") for m in llm_list]
    llm_alias = st.selectbox("LLM (Ollama)", options=llm_aliases, index=0, key="ask_llm_alias")
with c2:
    top_k = st.number_input("Top-K (Kontext-Passagen)", min_value=1, max_value=20, value=top_k_default, step=1)
question = st.text_area("Frage an die Arbeit", height=120, key="ask_question")
send = st.button("Frage senden", type="primary", use_container_width=True)

# ---- Prompt/Context Helfer ----
_SYSTEM_INSTRUCT = (
    "Du bist ein strenger Assistent. Antworte ausschließlich auf Basis des bereitgestellten KONTEKSTS.\n"
    "Wenn die Information nicht eindeutig im Kontext steht, antworte genau mit: Nicht im Kontext enthalten.\n"
    "Antworte präzise und kurz auf Deutsch."
)
def _llm_from_alias(alias: str):
    cfgs = [m for m in llm_list if (m.get("alias") or m.get("model")) == alias]
    if not cfgs: return None, {}
    m = cfgs[0]; params = dict(m.get("params") or {}); params.setdefault("temperature", 0)
    return m.get("model"), params

def _meta_preamble(meta: dict, docid_val: str) -> str:
    return (
        "### Metadaten der Arbeit\n"
        f"- docid: {docid_val}\n"
        f"- Studierende/r: {meta.get('student_name','–')}\n"
        f"- Titel: {meta.get('thesis_title','–')}\n"
        f"- Arbeitstyp: {meta.get('work_type','–')}\n"
        f"- Abgabedatum: {meta.get('submission_date','–')}\n"
        f"- Erstprüfer/in: {meta.get('examiner_first','–')}\n"
        f"- Zweitprüfer/in: {meta.get('examiner_second','–')}\n"
        f"- Studiengang: {meta.get('study_program','–')}\n"
    ).strip()

def _strict_prompt(q: str, ctx: str) -> str:
    return f"{_SYSTEM_INSTRUCT}\n\nKONTEXT:\n{ctx}\n\nFRAGE:\n{q}\n\nANTWORT:"

def _search_with_context(q: str, k: int) -> dict:
    try:
        from app.services.search_facade import SearchFacade
        s = SearchFacade(cfg, model_reg)
        try: return s.search(q, work_type=work_type, docid=docid, top_k=k) or {}
        except TypeError: return s.search(q, docid=docid, top_k=k) or {}
    except Exception as e:
        log.warning("search_failed", extra={"extra_fields": {"err": str(e)}}); return {}

# ---- Ausführung ----
answer_box, sources_box = st.empty(), st.empty()
if send:
    if not question.strip():
        st.warning("Bitte zuerst eine Frage eingeben."); st.stop()
    with st.spinner("Verarbeite Anfrage…"):
        # 1) Retrieval
        search_res = _search_with_context(question, int(top_k))
        retrieved_context = (search_res.get("context") or "").strip()
        sources = search_res.get("sources") or []
        collection = search_res.get("collection") or f"thesis_{work_type}_parents"
        # 2) Kontext zusammenbauen
        meta_ctx = _meta_preamble(md, docid)
        full_ctx = f"{meta_ctx}\n\n### Text-Kontext (Ausschnitte)\n{retrieved_context}".strip()
        # 3) LLM-Aufruf
        model_name, options = _llm_from_alias(llm_alias)
        if not model_name:
            st.error("Ausgewähltes LLM konnte nicht aufgelöst werden.")
        else:
            base_url = (cfg.get("ollama") or {}).get("url") or (cfg.get("ollama") or {}).get("base_url") or "http://host.docker.internal:11434"
            client = OllamaClient(base_url)
            prompt = _strict_prompt(question.strip(), full_ctx)
            try:
                resp = client.generate(model=model_name, prompt=prompt, options=options)
                answer_box.markdown(f"**Antwort:**\n\n{resp}")
            except Exception as e:
                log.error("llm_generate_failed", extra={"extra_fields": {"err": str(e)}})
                st.error(f"LLM-Antwort fehlgeschlagen: {e}")
            if sources:
                with sources_box.expander("Quellen (Kontextpassagen)"): st.table(sources)
        # 4) Kontext, Prompt & Parameter sichtbar machen
        with st.expander("📄 Kontext anzeigen"):
            st.write("**Metadaten-Kontext**"); st.text(meta_ctx)
            st.write("**Retrieval-Kontext (Ausschnitte)**"); st.text(retrieved_context if retrieved_context else "—")
            st.write("**Kombinierter Kontext (an das LLM gegeben)**"); st.text(full_ctx)
        with st.expander("🧠 Prompt & System-Instruktion"):
            st.write("**System-Prompt**"); st.text(_SYSTEM_INSTRUCT)
            st.write("**Finaler Prompt (an das LLM gesendet)**"); st.text(prompt)
        with st.expander("⚙️ Parameter & Laufzeitkonfiguration"):
            llm_cfg = next((m for m in llm_list if (m.get("alias") or m.get("model")) == llm_alias), {})
            params_view = dict(llm_cfg.get("params") or {}); params_view.setdefault("temperature", options.get("temperature", 0))
            st.json({
                "docid": docid, "work_type": work_type, "collection": collection, "top_k": int(top_k),
                "ollama_url": base_url, "llm_alias": llm_alias, "llm_model": llm_cfg.get("model"),
                "llm_params": params_view, "embedding_alias": emb_alias,
                "embedding_model": (emb_cfg or {}).get("model"),
                "embedding_dim": (emb_cfg or {}).get("dim"),
                "embedding_normalize": (emb_cfg or {}).get("normalize"),
            })
        # 5) Optionale Gegenprobe (Chroma)
        with st.expander("🔎 Technische Gegenprobe (Chroma)"):
            diag = {}
            try:
                if not emb_cfg: diag["error"] = "Kein Embedding-Config für den aktiven Alias gefunden."
                else:
                    fac = EmbeddingsFactory(cfg, emb_cfg)
                    vec = fac.embed_robust([question.strip()])[0]
                    chroma = ChromaWrapper(cfg.get("chroma") or {})
                    col = chroma.get_or_create_collection(collection)
                    raw = col.query(query_embeddings=[vec], n_results=int(top_k), where={"docid": docid})
                    docs = raw.get("documents") or []; metas = raw.get("metadatas") or []
                    if docs and isinstance(docs[0], list): docs = docs[0]
                    if metas and isinstance(metas[0], list): metas = metas[0]
                    diag.update({"hits": len(docs), "first_text_len": len((docs[0] or "")) if docs else 0,
                                 "first_meta_keys": list(metas[0].keys()) if metas else []})
            except Exception as e:
                diag["exception"] = str(e)
            st.json(diag)
