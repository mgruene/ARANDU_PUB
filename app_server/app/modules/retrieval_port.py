# app/modules/retrieval_port.py
# Adapter, um vorhandene Suche (search_facade) zu nutzen.
from typing import Dict, Any

def try_search(payload: Dict[str,Any]) -> Dict[str,Any]:
    """
    payload: {'query','doc_id','top_k'}
    returns: {'context': str, 'chunks': list}
    """
    try:
        from app.services.search_facade import query as search_query  # erwartete Signatur im Projekt
        res = search_query({"query": payload.get("query",""),
                            "doc_id": payload.get("doc_id"),
                            "top_k": payload.get("top_k",5)})
        ctx = "\n\n".join([c.get("text","") for c in res.get("chunks",[])])
        return {"context": ctx[:8000], "chunks": res.get("chunks",[])}
    except Exception:
        return {"context": "", "chunks": []}
