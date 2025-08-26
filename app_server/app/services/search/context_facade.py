# services/search/context_facade.py
from typing import Dict, Any, List
from app.modules.logging_setup import get_logger

log = get_logger("search.context_facade")


class ContextFacade:
    """Kontextaufbau aus Treffern (Parents zuerst, dann Children) mit Zeichenlimit."""

    def assemble(self, parents: List[Dict[str, Any]], children: List[Dict[str, Any]], max_chars: int) -> Dict[str, Any]:
        buf: List[str] = []
        sources: List[Dict[str, Any]] = []
        total = 0

        def add(hit: Dict[str, Any]) -> bool:
            nonlocal total
            text = (hit.get("document") or "").strip()
            if not text:
                return True
            nxt = total + len(text) + 2
            if nxt > max_chars and total > 0:
                return False
            buf.append(text)
            total = nxt
            md = hit.get("metadata") or {}
            sources.append({
                "id": hit.get("id"),
                "distance": hit.get("distance"),
                "page": md.get("page"),
                "section": md.get("section"),
                "docid": md.get("docid"),
            })
            return True

        for h in parents:
            if not add(h):
                break
        for h in children:
            if not add(h):
                break

        context = "\n\n".join(buf)
        out = {"context": context, "sources": sources, "chars": len(context)}
        log.info("context_built", extra={"extra_fields": {"chars": out["chars"], "sources": len(sources)}})
        return out
