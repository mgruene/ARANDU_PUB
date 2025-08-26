# services/ingest/receipt_facade.py
from typing import Dict, Any
from datetime import datetime, timezone

class ReceiptIngestFacade:
    def build(
        self,
        docid: str,
        final_md: Dict[str, Any],
        file_info: Dict[str, Any],
        parents: Dict[str, Any],
        children: Dict[str, Any],
        confidence_md: Dict[str, Any],
        source_md: Dict[str, Any],
        embedding_alias: str,
        embedding_model: str,
        embedding_dim: int,
        embedding_normalize: bool,
        collections: Dict[str, Any],
        counts: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "docid": docid,
            "filename": file_info.get("pdf_path"),
            "work_type": final_md.get("work_type"),
            "collections": collections,
            "counts": counts,
            "embedding_alias": embedding_alias,
            "embedding_model": embedding_model,
            "embedding_dim": embedding_dim,
            "embedding_normalize": embedding_normalize,
            "ingest_at": datetime.now(timezone.utc).isoformat(),
            "metadata": final_md,
            "confidence": confidence_md,
            "sources": source_md,
        }
