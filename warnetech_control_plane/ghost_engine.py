"""Ghost copy creation, storage layout, retrieval, metadata indexing,
embedding generation, and AI-driven recall.

A "ghost copy" is a slice (see slice_engine.Slice) preserved past the point
where its raw data would normally be dropped by retention_engine — the
control plane's answer to "keep a compressed, addressable memory of
everything without paying hot-tier storage cost forever."

Storage layout: ``ghost/{yyyy}/{mm}/{domain}/{slice_id}.bin``

Embeddings default to a deterministic hash-based projection so recall works
with zero external dependencies; pass a real `embed_fn` (e.g. a sentence
transformer or hosted embedding API) for production-quality semantic recall.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Optional

from .config import ControlPlaneConfig, DEFAULT_CONFIG
from .logging import get_logger
from .slice_engine import Slice
from .utils import now_iso, read_json, write_json

logger = get_logger(__name__)

EmbedFn = Callable[[str], list[float]]


def _default_embed(text: str, dims: int = 32) -> list[float]:
    """A cheap, deterministic, dependency-free embedding: hashes the text
    into `dims` floats. Preserves near-duplicate detection (identical text
    -> identical vector) but has none of the semantic properties of a real
    embedding model — swap it out via `embed_fn` for anything beyond exact
    or near-exact recall.
    """
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    # Repeat the digest to cover `dims` floats, then normalize to unit length.
    raw = (digest * ((dims // len(digest)) + 1))[:dims]
    vec = [b / 255.0 for b in raw]
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)


@dataclass
class GhostIndexEntry:
    slice_id: str
    domain: str
    path: str
    embedding: list[float]
    summary: str
    indexed_at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict:
        return asdict(self)


class GhostEngine:
    def __init__(self, config: ControlPlaneConfig = DEFAULT_CONFIG, embed_fn: Optional[EmbedFn] = None) -> None:
        self._config = config
        self._embed_fn = embed_fn or _default_embed
        self._base_dir = Path(config.local_backup_dir) / "ghost"
        self._index_path = self._base_dir / "index.json"

    # -- storage layout --------------------------------------------------------

    def _path_for(self, slice_obj: Slice) -> Path:
        created = slice_obj.metadata.created_at  # "2026-08-05T13:11:17Z"
        year, month = created[0:4], created[5:7]
        return self._base_dir / year / month / slice_obj.metadata.domain / f"{slice_obj.metadata.slice_id}.bin"

    # -- create / retrieve --------------------------------------------------------

    def create_ghost_copy(self, slice_obj: Slice, summary: str) -> GhostIndexEntry:
        path = self._path_for(slice_obj)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(slice_obj.body)

        embedding = self._embed_fn(summary)
        entry = GhostIndexEntry(
            slice_id=slice_obj.metadata.slice_id,
            domain=slice_obj.metadata.domain,
            path=str(path),
            embedding=embedding,
            summary=summary,
        )
        self._append_index(entry)
        logger.info("ghost copy created", slice_id=entry.slice_id, path=entry.path)
        return entry

    def retrieve_ghost_copy(self, slice_id: str) -> Optional[bytes]:
        entry = self._find_index_entry(slice_id)
        if entry is None:
            return None
        path = Path(entry["path"])
        if not path.exists():
            logger.error("ghost copy indexed but missing on disk", slice_id=slice_id, path=str(path))
            return None
        return path.read_bytes()

    # -- metadata index -----------------------------------------------------------

    def _load_index(self) -> list[dict]:
        if not self._index_path.exists():
            return []
        return read_json(self._index_path)

    def _append_index(self, entry: GhostIndexEntry) -> None:
        index = self._load_index()
        index.append(entry.to_dict())
        write_json(self._index_path, index)

    def _find_index_entry(self, slice_id: str) -> Optional[dict]:
        for entry in self._load_index():
            if entry["slice_id"] == slice_id:
                return entry
        return None

    # -- embeddings / recall --------------------------------------------------------

    def generate_embedding(self, text: str) -> list[float]:
        return self._embed_fn(text)

    def ai_recall(self, query: str, top_k: int = 5) -> list[dict]:
        """Naive cosine-similarity search over the ghost index. Fine for the
        index sizes this control plane expects (ghost tier is aggregates,
        not raw events); swap for a vector index if that assumption changes.
        """
        query_vec = self._embed_fn(query)
        scored = [
            {**entry, "similarity": _cosine_similarity(query_vec, entry["embedding"])}
            for entry in self._load_index()
        ]
        scored.sort(key=lambda e: e["similarity"], reverse=True)
        return scored[:top_k]
