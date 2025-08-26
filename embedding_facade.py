# services/ingest/embedding_facade.py
from typing import Dict, Any
from modules.embeddings_factory import EmbeddingsFactory
from modules.logging_setup import get_logger

log = get_logger("embedding_ingest_facade")

class EmbeddingIngestFacade:
    def __init__(self, app_cfg: Dict[str, Any], model_reg):
        self.app_cfg = app_cfg
        self.model_reg = model_reg

    def build(self, retrieval_cfg: Dict[str, Any], parents: Dict[str, Any], children: Dict[str, Any]) -> Dict[str, Any]:
        """Ermittelt Embedding-Config und berechnet Vektoren für Parents/Children.
        Rückgabe enthält zusätzlich technische Embedding-Metadaten.
        """
        alias = retrieval_cfg.get("embedding_alias_default", "default")

        # Konfiguration sicher aus dem ModelRegistry holen
        cfg = getattr(self.model_reg, "_cfg", {}) or {}
        emb_cfg = None
        for e in cfg.get("embeddings", []) or []:
            if e.get("alias") == alias:
                emb_cfg = e
                break
        if not emb_cfg:
            raise ValueError(f"Embedding-Config für Alias '{alias}' nicht gefunden")

        # WICHTIG: EmbeddingsFactory erwartet app_cfg, NICHT ModelRegistry
        fac = EmbeddingsFactory(self.app_cfg, emb_cfg)

        # Eltern/Kind-Embeddings berechnen
        parents_vecs = fac.embed_robust(parents["texts"])
        children_vecs = fac.embed_robust(children["texts"])
        parents["embeddings"] = parents_vecs
        children["embeddings"] = children_vecs

        log.info("embeddings_built", extra={"extra_fields": {
            "alias": alias, "parents": len(parents_vecs), "children": len(children_vecs)
        }})

        return {
            "alias_used": alias,
            "model": emb_cfg.get("model"),
            "dim": emb_cfg.get("dim"),
            "normalize": emb_cfg.get("normalize"),
        }
