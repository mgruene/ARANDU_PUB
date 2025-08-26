# modules/ingest/receipt.py
from typing import Dict, Any

def build_receipt(docid: str, work_type: str, file_basename: str,
                  collections: Dict[str, str], counts: Dict[str, int],
                  embedding_alias: str, final_metadata: Dict[str, Any],
                  confidence: Dict[str, Any], source: str, filehash: str) -> Dict[str, Any]:
    return {
        "docid": docid,
        "file": file_basename,
        "work_type": work_type,
        "collections": collections,
        "counts": counts,
        "embedding_alias": embedding_alias,
        "metadata": final_metadata,
        "confidence": confidence or {},
        "source": source or "",
        "filehash": filehash,
        "status": "ingested_parent_child",
    }
