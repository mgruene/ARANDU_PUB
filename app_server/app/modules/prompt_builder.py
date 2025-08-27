# app/modules/prompt_builder.py
# Baut einen Bewertungs-Prompt aus Rubrik, Kontext und Beispielen
from typing import Dict, Any, List

def _fmt_examples(examples: List[Dict[str, Any]], max_len: int=2000) -> str:
    if not examples: return ""
    lines=[]
    for e in examples[:6]:
        tag = "POS" if e.get("label")=="positive" else "NEG"
        src = e.get("source",{})
        src_txt = f" (doc:{src.get('doc_id')} chunk:{src.get('chunk_id')})" if src else ""
        text = (e.get("text","").strip().replace("\n"," "))[:400]
        lines.append(f"- [{tag}]{src_txt} {text}")
    joined = "\n".join(lines)
    return joined[:max_len]

def build_prompt(inp: Dict[str, Any]) -> Dict[str, Any]:
    """
    inp: { 'rubric': {...}, 'question': str, 'context': str, 'examples': [..] }
    -> { 'system': str, 'user': str, 'metadata': {...} }
    """
    rubric = inp.get("rubric", {})
    ctx = inp.get("context", "")
    q = inp.get("question", "Bewerte den Text gemäß Kriterium.")
    ex = inp.get("examples", [])
    rubric_name = rubric.get("name", "Rubrik")
    rubric_desc = rubric.get("description", "")
    example_block = _fmt_examples(ex)
    system = """Du bist ein strenger, aber faire:r Gutachter:in.
Bewerte ausschließlich auf Basis des gegebenen Kontexts und des Kriteriums.
Antworte strukturiert: (1) Kurzurteil, (2) Begründung mit Belegen (Zeilen-/Satz-Zitate), (3) Verbesserungshinweise."""
    user = f"""Kriterium: {rubric_name}
Beschreibung: {rubric_desc}
Beispiele:
{example_block or "- (keine Beispiele hinterlegt)"} 

Frage/Auftrag: {q}

Kontext (Auszüge aus der Arbeit):
\"\"\"{ctx}\"\"\""""
    return {"system": system.strip(), "user": user.strip(), "metadata":{"rubric_id": rubric.get("id")}}
