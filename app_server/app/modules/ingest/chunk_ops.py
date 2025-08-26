# app/modules/ingest/chunk_ops.py
# Auto-generated split from original chunk_ops.py — no logic changes, only relocation.

# Facade: re-exports original functions from split modules.

# app/modules/ingest/chunk_ops.py
# Child-/Parent-Aufbereitung für den Ingest.
# - align_and_prune_children: richtet Tripel (docs/ids/metadatas) aus, repariert None-Metadaten
#   und füllt fehlende chunk_index-Werte.
# - filter_chunks_minlen: entfernt sehr kurze Chunks.
# - build_children: erzeugt Child-Docs/IDs/Metadaten.
# - build_parents: gruppiert Children zu Parents und legt Parent-Metadaten an.

from typing import Dict, Any, List, Tuple
import json
import re

from modules.logging_setup import get_logger
from modules.chunking import chunk_text
from modules.parent_chunking import make_parents_from_children

log = get_logger("ingest.chunk_ops")

_ID_IDX_RE = re.compile(r"_c_(\d{4})$")

from .filters import align_and_prune_children, filter_chunks_minlen  # re-export
from .parent_grouping import build_parents  # re-export
from .splitters import _infer_chunk_index, build_children  # re-export
