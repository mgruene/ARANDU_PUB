# services/ingest_facade.py
# Minimalinvasiv modularisiert: Orchestrierung über Sub-Fassaden (services/ingest/*)

from typing import Dict, Any
import os

from modules.logging_setup import get_logger
from modules.model_registry import ModelRegistry
from modules.chroma_client import ChromaWrapper
from services.state_facade import StateFacade

# Sub-Fassaden
from services.ingest.metadata_facade import MetadataIngestFacade
from services.ingest.file_facade import FileIngestFacade
from services.ingest.pdf_facade import PDFIngestFacade
from services.ingest.chunk_facade import ChunkIngestFacade
from services.ingest.embedding_facade import EmbeddingIngestFacade
from services.ingest.upsert_facade import UpsertIngestFacade
from services.ingest.receipt_facade import ReceiptIngestFacade

# Sanitizing (Chroma erwartet primitive Typen)
from modules.ingest.metadata_ops import sanitize_metadata

log = get_logger("ingest_facade")

class IngestFacade:
    def __init__(self, app_cfg: Dict[str, Any], model_reg: ModelRegistry):
        self.app_cfg = app_cfg
        self.model_reg = model_reg
        self.chroma = ChromaWrapper(app_cfg["chroma"])  # REST/HTTP Wrapper laut bestehender Architektur
        self.state = StateFacade(app_cfg["paths"]["app_state_dir"])
        os.makedirs(self.app_cfg["paths"]["uploads_dir"], exist_ok=True)
        log.info("ingest_facade_init", extra={"extra_fields": {"uploads_dir": self.app_cfg["paths"]["uploads_dir"]}})

        # Sub-Fassaden
        self.meta = MetadataIngestFacade()
        self.files = FileIngestFacade(app_cfg)
        self.pdf = PDFIngestFacade()
        self.chunk = ChunkIngestFacade()
        self.embed = EmbeddingIngestFacade(app_cfg, model_reg)
        self.upsert = UpsertIngestFacade(self.chroma)
        self.receipt = ReceiptIngestFacade()

    def ingest(self, pdf_bytes: bytes, filename: str, metadata_in: Dict[str, Any], docid: str) -> Dict[str, Any]:
        """Transaction Script: PDF→Metadaten→Chunks→Embeddings→Upsert→Receipt/Index.
        Rückgabe bleibt unverändert (Quittungs-Dict).
        """
        # 1) Metadaten finalisieren (Regex/Heuristik bereits erfolgt; hier Normalisierung/IDs)
        final_md, confidence_md, source_md = self.meta.prepare(metadata_in, docid)

        # 2) Datei & Metadaten persistieren (Upload-Verzeichnis + JSONs)
        file_info = self.files.save(
            pdf_bytes=pdf_bytes,
            filename=filename,
            docid=docid,
            final_md=final_md,
            confidence_md=confidence_md,
            source_md=source_md,
        )

        # 3) PDF-Text extrahieren
        full_text = self.pdf.extract(pdf_bytes)

        # 4) Retrieval-Konfiguration (aus model_config.json via ModelRegistry)
        retrieval = self.model_reg.retrieval() or {}
        log.info("retrieval_cfg_active", extra={"extra_fields": {
            "child_size": retrieval.get("child_chunk_size"),
            "child_overlap": retrieval.get("child_chunk_overlap"),
            "parent_size": retrieval.get("parent_group_size"),
            "parent_overlap": retrieval.get("parent_group_overlap"),
            "emb_alias": retrieval.get("embedding_alias_default"),
            "emb_fallbacks": retrieval.get("embedding_alias_fallbacks"),
        }})

        # 5) Children/Parents erstellen
        children, parents = self.chunk.build(
            full_text=full_text,
            final_md=final_md,
            docid=docid,
            source_file=os.path.basename(file_info["pdf_path"]),
            child_size=int(retrieval.get("child_chunk_size", 1200)),
            child_overlap=int(retrieval.get("child_chunk_overlap", 200)),
            parent_group_size=int(retrieval.get("parent_group_size", 3)),
            parent_group_overlap=int(retrieval.get("parent_group_overlap", 1)),
        )

        # 6) Embeddings berechnen (liefert auch Modell-Metadaten zurück)
        emb_res = self.embed.build(retrieval_cfg=retrieval, parents=parents, children=children)
        emb_alias_used = emb_res.get("alias_used")
        emb_model = emb_res.get("model")
        emb_dim = emb_res.get("dim")
        emb_norm = emb_res.get("normalize")

        # 7) Chunk-Metadaten sanitisieren + um fachliche/technische Felder anreichern
        def _enrich(meta: Dict[str, Any], kind: str) -> Dict[str, Any]:
            m = sanitize_metadata(meta, kind)
            # technische Metadaten
            m["embedding_alias"] = emb_alias_used
            m["embedding_model"] = emb_model
            m["embedding_dim"] = emb_dim
            m["embedding_normalize"] = emb_norm
            # fachliche Metadaten (Student/Titel/etc.)
            m.update(final_md)
            return m

        parents["metadatas"] = [_enrich(m, "parent") for m in (parents.get("metadatas") or [])]
        children["metadatas"] = [_enrich(m, "child") for m in (children.get("metadatas") or [])]

        # 8) Upsert nach Chroma
        collections, counts = self.upsert.run(
            docid=docid,
            final_md=final_md,
            parents=parents,
            emb_res=emb_res,
            children=children,
        )

        # 9) Quittung erzeugen + State aktualisieren
        receipt = self.receipt.build(
            docid=docid,
            final_md=final_md,
            file_info=file_info,
            parents=parents,
            children=children,
            confidence_md=confidence_md,
            source_md=source_md,
            embedding_alias=emb_alias_used,
            embedding_model=emb_model,
            embedding_dim=emb_dim,
            embedding_normalize=emb_norm,
            collections=collections,
            counts=counts,
        )
        self.state.save_ingest_receipt(receipt)
        self.state.update_index_from_receipt(receipt)
        log.info("ingest_receipt", extra={"extra_fields": {"docid": docid, "collections": collections, "counts": counts}})
        return receipt
