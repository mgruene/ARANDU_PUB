# services/ingest/embedding_facade.py
from typing import Dict, Any, List
from modules.embeddings_factory import EmbeddingsFactory
from modules.logging_setup import get_logger

log = get_logger("embedding_ingest_facade")

class EmbeddingIngestFacade:
    def __init__(self, app_cfg: Dict[str, Any], model_reg):
        self.app_cfg = app_cfg
        self.model_reg = model_reg

    def _resolve_embedding_cfg(self, retrieval_cfg: Dict[str, Any]) -> Dict[str, Any]:
        alias = (
            retrieval_cfg.get("embedding_alias_default")
            or retrieval_cfg.get("embedding_alias")
            or "default"
        )
        cfg = getattr(self.model_reg, "_cfg", {}) or {}
        emb_list = cfg.get("embeddings", []) or []
        emb_cfg = next((e for e in emb_list if e.get("alias") == alias), None)
        if not emb_cfg:
            raise ValueError(f"Embedding-Config für Alias '{alias}' nicht gefunden")
        return emb_cfg

    def build(self, retrieval_cfg: Dict[str, Any], parents: Dict[str, Any], children: Dict[str, Any]) -> Dict[str, Any]:
        """
        Berechnet Embeddings für Parents (Pflicht) und optional Children.
        Achtung: richtet Parents-Dokumente/Metadaten auf die tatsächlich eingebetteten Texte aus,
        damit Längen mit IDs/Vektoren für den Upsert übereinstimmen.
        Rückgabe liefert zusätzliche technische Metadaten + IDs/Vektoren der Parents.
        """
        emb_cfg = self._resolve_embedding_cfg(retrieval_cfg)

        # WICHTIG: EmbeddingsFactory erwartet app_cfg, NICHT ModelRegistry
        fac = EmbeddingsFactory(self.app_cfg, emb_cfg)

        # --- Parents vorbereiten ---
        p_docs: List[str] = list(parents.get("documents") or [])
        p_mds:  List[Dict[str, Any]] = list(parents.get("metadatas") or [])
        p_ids:  List[str] = list(parents.get("ids") or [])

        kept_docs: List[str] = []
        kept_mds:  List[Dict[str, Any]] = []
        kept_ids:  List[str] = []

        for i, t in enumerate(p_docs):
            txt = (t or "").strip()
            if not txt:
                # leere Parent-Texte überspringen (Sicherheitsnetz)
                continue
            kept_docs.append(txt)
            kept_mds.append(p_mds[i] if i < len(p_mds) else {})
            kept_ids.append(p_ids[i] if i < len(p_ids) else f"p_{i:04d}")

        # Embeddings für Parents
        vectors_parent: List[List[float]] = fac.embed_robust(kept_docs) if kept_docs else []

        # Parents in-place angleichen (damit Upsert-Längen stimmen)
        parents["documents"]  = kept_docs
        parents["metadatas"]  = kept_mds
        # Hinweis: Upsert nimmt die Parent-IDs aus emb_res["filtered_ids_parent"],
        # daher müssen wir parents["ids"] nicht zwingend überschreiben.

        # --- Children optional (werden bei dir ohne Embeddings upserted) ---
        c_docs: List[str] = list(children.get("documents") or [])
        try:
            children["embeddings"] = fac.embed_robust(c_docs) if c_docs else []
        except Exception as e:
            # nicht kritisch für Upsert; nur Loggen
            log.warning("child_embed_failed", extra={"extra_fields": {"err": str(e)}})
            children["embeddings"] = []

        log.info(
            "embeddings_built",
            extra={"extra_fields": {
                "alias": emb_cfg.get("alias"),
                "parents_docs": len(kept_docs),
                "children_docs": len(c_docs),
            }}
        )

        return {
            "alias_used": emb_cfg.get("alias"),
            "model": emb_cfg.get("model"),
            "dim": emb_cfg.get("dim"),
            "normalize": emb_cfg.get("normalize"),
            "filtered_ids_parent": kept_ids,
            "vectors_parent": vectors_parent,
        }
