# app_server/app/ui/pages/06_admin_rubrics.py
# ARANDU – Admin: Rubriken (zentriert, robustes DataFrame, LLM-Alias aus model_config)
import os, json, datetime
from typing import Any, Dict, List, Tuple, Optional
import pandas as pd
import streamlit as st
from app.modules.model_registry import ModelRegistry

# ------------------------ Helper ------------------------

def _cfg_dir() -> str:
    v = os.getenv("ARANDU_CFG_DIR", "config")
    if v.startswith("/"): return v
    for base in ("/data", "/code/data"):
        p = os.path.join(base, v)
        if os.path.isdir(p): return p
    return v

def _load(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

def _save(path: str, data: Dict[str, Any]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def _now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _flatten(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    def rec(lst, pref: List[int], path: List[int]):
        for i, n in enumerate(lst, 1):
            rows.append({
                "num": ".".join(map(str, pref+[i])),
                "level": len(pref)+1,
                "path": path+[i-1],
                "id": n.get("id",""),
                "name": n.get("name",""),
                "description": n.get("description",""),
                "llm_alias": n.get("llm_alias",""),
                "top_k": n.get("top_k", ""),  # kann int oder "" sein -> später zu str
                "children_count": len(n.get("children") or [])
            })
            kids = n.get("children") or []
            if kids: rec(kids, pref+[i], path+[i-1])
    rec(nodes, [], [])
    return rows

def _parent_and_idx(root: List[Dict[str, Any]], path: List[int]) -> Tuple[List[Dict[str, Any]], int]:
    parent = root
    for p in path[:-1]: parent = parent[p].setdefault("children", [])
    return parent, path[-1]

def _by_path(root: List[Dict[str, Any]], path: List[int]) -> Dict[str, Any]:
    node, cur = None, root
    for p in path: node, cur = cur[p], cur[p].setdefault("children", [])
    return node

def _gen_id(name: str, existing: set) -> str:
    base = "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_") or "rubric"
    rid, i = base, 2
    while rid in existing: rid, i = f"{base}_{i}", i+1
    return rid

def _can_add_child(node: Dict[str, Any]) -> bool:
    return len(node.get("children") or []) < 2

def _llm_alias_options(registry: ModelRegistry) -> List[str]:
    # Nur freigegebene Rubriken-Modelle
    return [m["alias"] for m in registry.list_llms(True) if m.get("alias")]

# ------------------------ Page ------------------------

st.set_page_config(page_title="Rubriken – Admin", layout="wide")
st.title("Rubriken – Verwaltung")

L, M, R = st.columns([1,3,1])
with M:
    cfgd = _cfg_dir()
    rubrics_path = os.path.join(cfgd, "rubrics_config.json")
    rubcfg = _load(rubrics_path)
    rubrics = rubcfg.get("rubrics", [])

    # LLM-Aliasse aus Registry
    registry = ModelRegistry(cfgd)
    llm_aliases = _llm_alias_options(registry)

    st.caption(f"Rubriken: {rubrics_path} · Version: {rubcfg.get('version','?')} · Stand: {rubcfg.get('updated_at','-')}")

    rows = _flatten(rubrics)
    if rows:
        st.subheader("Aktuelle Rubriken")

        # --- Arrow/Pandas robust machen: Spalten sauber als String casten
        def _s(x): 
            if x is None: return ""
            # ints sauber zu String
            if isinstance(x, int): return str(x)
            return str(x)
        df = pd.DataFrame({
            "Nummer": [r["num"] for r in rows],
            "ID": [r["id"] for r in rows],
            "Name": [r["name"] for r in rows],
            "Beschreibung": [r["description"] for r in rows],
            "LLM-Alias": [_s(r["llm_alias"]) for r in rows],
            "top_k": [_s(r["top_k"]) for r in rows],
            "Kinder": [str(r["children_count"]) for r in rows],
        })
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("Noch keine Rubriken hinterlegt.")
    st.divider()

    st.subheader("Bearbeiten")
    opts = [{"label": f"{r['num']} – {r['name']} [{r['id']}]", "path": r["path"]} for r in rows]
    sel = st.selectbox("Rubrik auswählen", [None]+opts, format_func=lambda o: o["label"] if o else "(keine)", index=0, key="rubrics_select_obj")
    path = sel["path"] if sel else None

    c1,c2,c3,c4,_ = st.columns(5)
    if c1.button("↑ Nach oben", use_container_width=True, disabled=path is None):
        parent, i = _parent_and_idx(rubrics, path)  # type: ignore
        if i>0:
            parent[i-1], parent[i] = parent[i], parent[i-1]
            rubcfg["updated_at"]=_now(); _save(rubrics_path, rubcfg)
            st.success("Verschoben (↑)."); st.rerun()

    if c2.button("↓ Nach unten", use_container_width=True, disabled=path is None):
        parent, i = _parent_and_idx(rubrics, path)  # type: ignore
        if i<len(parent)-1:
            parent[i+1], parent[i] = parent[i], parent[i+1]
            rubcfg["updated_at"]=_now(); _save(rubrics_path, rubcfg)
            st.success("Verschoben (↓)."); st.rerun()

    if c3.button("➕ Unterkategorie", use_container_width=True, disabled=path is None):
        node = _by_path(rubrics, path)  # type: ignore
        level = len(path)+1  # type: ignore
        if level>=3: st.warning("Maximal 3 Ebenen (1.1.1).")
        elif not _can_add_child(node): st.warning("Max. 2 Unterkategorien pro Ebene.")
        else:
            existing = {r["id"] for r in rows}
            node.setdefault("children", []).append({"id": _gen_id("unterkategorie", existing), "name":"Neue Unterkategorie", "description": ""})
            rubcfg["updated_at"]=_now(); _save(rubrics_path, rubcfg)
            st.success("Unterkategorie angelegt."); st.rerun()

    if c4.button("🗑️ Löschen", use_container_width=True, disabled=path is None):
        parent, i = _parent_and_idx(rubrics, path)  # type: ignore
        del parent[i]; rubcfg["updated_at"]=_now(); _save(rubrics_path, rubcfg)
        st.success("Gelöscht."); st.rerun()

    st.divider()

    # Neue Hauptkategorie
    with st.expander("Neue Hauptkategorie anlegen"):
        with st.form("new_root"):
            name = st.text_input("Name", "")
            desc = st.text_area("Beschreibung", "")
            llm_alias = st.selectbox("LLM-Alias (optional)", [""]+llm_aliases, index=0, key="new_root_llm")
            top_k = st.number_input("top_k (optional)", 0, 20, 0, 1)
            if st.form_submit_button("Anlegen"):
                if not name.strip(): st.warning("Bitte Name angeben.")
                else:
                    rid = _gen_id(name, {r["id"] for r in rows})
                    node = {"id": rid, "name": name.strip(), "description": desc.strip()}
                    if llm_alias.strip(): node["llm_alias"]=llm_alias.strip()
                    if top_k>0: node["top_k"]=int(top_k)
                    rubrics.append(node); rubcfg["updated_at"]=_now(); _save(rubrics_path, rubcfg)
                    st.success(f"Hauptkategorie '{name}' angelegt."); st.rerun()

    # Ausgewählte bearbeiten
    st.subheader("Ausgewählte Rubrik bearbeiten")
    if not path:
        st.info("Bitte oben eine Rubrik auswählen.")
    else:
        node = _by_path(rubrics, path)
        with st.form("edit_node"):
            name = st.text_input("Name", node.get("name",""))
            desc = st.text_area("Beschreibung", node.get("description",""))
            cur = node.get("llm_alias","")
            llm_alias = st.selectbox("LLM-Alias (optional)", [""]+llm_aliases,
                                     index=([""]+llm_aliases).index(cur) if cur in llm_aliases else 0,
                                     key="edit_node_llm")
            top_k_val = int(node.get("top_k") or 0)
            top_k = st.number_input("top_k (optional)", 0, 20, top_k_val, 1)
            if st.form_submit_button("Änderungen speichern"):
                node["name"]=name.strip(); node["description"]=desc.strip()
                if llm_alias.strip(): node["llm_alias"]=llm_alias.strip()
                else: node.pop("llm_alias", None)
                if top_k>0: node["top_k"]=int(top_k)
                else: node.pop("top_k", None)
                rubcfg["updated_at"]=_now(); _save(rubrics_path, rubcfg)
                st.success("Gespeichert."); st.rerun()
