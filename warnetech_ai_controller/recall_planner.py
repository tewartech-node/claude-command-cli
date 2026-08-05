"""Reconstruction planning: given a query, determines the minimal set of
slices (or ghost copies) needed to satisfy it.
"""

from __future__ import annotations

from typing import Any, Optional

from .config import AIControllerConfig, DEFAULT_CONFIG
from .utils import cosine_similarity, now_iso


def plan_recall(query: dict, ranked_slices: list[dict], config: AIControllerConfig = DEFAULT_CONFIG) -> dict:
    """Greedily accepts slices in rank order (already sorted by the caller,
    typically via relevance.rank_by_similarity or rank_by_metadata) until
    either the configured coverage ratio of `query['total_data_size']` is
    reached or `recall.max_slices` is hit — whichever comes first.
    """
    total_size = query.get("total_data_size", 0)
    target_size = int(total_size * config.recall.target_coverage_ratio) if total_size else None

    selected: list[dict] = []
    accumulated = 0
    for entry in ranked_slices:
        if len(selected) >= config.recall.max_slices:
            break
        if target_size is not None and accumulated >= target_size:
            break
        selected.append(entry)
        accumulated += entry.get("size_bytes", 0)

    coverage_ratio = (accumulated / total_size) if total_size else None

    return {
        "query": query,
        "selected_slice_count": len(selected),
        "selected_data_size": accumulated,
        "total_data_size": total_size,
        "coverage_ratio": coverage_ratio,
        "meets_target": coverage_ratio is None or coverage_ratio <= config.recall.target_coverage_ratio,
        "slices": selected,
        "planned_at": now_iso(),
    }


def produce_recall_map(slices: list[dict]) -> dict:
    """Builds an ordered reconstruction map — the sequence and locations a
    caller should fetch/decrypt/decompress slices in. Time-ordered when
    every slice carries a `time_start`, otherwise preserves input order.
    """
    orderable = all("time_start" in s for s in slices)
    ordered = sorted(slices, key=lambda s: s["time_start"]) if orderable else list(slices)

    return {
        "order": "time" if orderable else "input",
        "steps": [
            {
                "sequence": i,
                "slice_id": s.get("slice_id"),
                "path": s.get("path"),
                "domain": s.get("domain"),
            }
            for i, s in enumerate(ordered)
        ],
        "total_steps": len(ordered),
    }


# ---------------------------------------------------------------------------
# Ghost copy recall planning
#
# Ghost copies (warnetech_control_plane.ghost_engine.GhostRecord dicts) have
# a different shape from slice metadata: no `size_bytes`, no `embedding` at
# the top level (it lives under `metadata["embedding"]`, set by
# ghost_engine.create_ghost_copy at write time), and `time_range` instead of
# `time_start`/`time_end`. Kept separate from plan_recall/produce_recall_map
# above rather than overloading them with branching on shape.
# ---------------------------------------------------------------------------


def plan_ghost_recall(
    ghost_copies: list[dict],
    query_embedding: Optional[list[float]] = None,
    config: AIControllerConfig = DEFAULT_CONFIG,
) -> dict:
    """Determines the minimal set of ghost copies needed to satisfy a
    recall request.

    With a `query_embedding`, ranks candidates by cosine similarity against
    each copy's `metadata["embedding"]` (set by ghost_engine at creation)
    and keeps only those above `config.relevance.min_similarity`. Without
    one, falls back to newest-first — a ghost copy carries no `size_bytes`
    to rank by like a plain slice, so recency is the next best signal.
    Either way the result is capped at `config.recall.max_slices`.
    """
    if query_embedding:
        scored = []
        for copy in ghost_copies:
            embedding = (copy.get("metadata") or {}).get("embedding", [])
            score = cosine_similarity(query_embedding, embedding) if embedding else 0.0
            if score >= config.relevance.min_similarity:
                scored.append({**copy, "similarity": score})
        scored.sort(key=lambda c: c["similarity"], reverse=True)
        ranked = scored
    else:
        ranked = sorted(ghost_copies, key=lambda c: c.get("created_at", ""), reverse=True)

    selected = ranked[: config.recall.max_slices]
    total_size = sum(c.get("size", 0) for c in selected)

    return {
        "selected_ghost_count": len(selected),
        "selected_total_size": total_size,
        "ghost_copies": selected,
        "recall_map": produce_ghost_recall_map(selected),
        "planned_at": now_iso(),
    }


def produce_ghost_recall_map(ghost_copies: list[dict]) -> dict:
    """Builds an ordered, control-plane-executable recall plan: one fetch
    step per ghost copy, oldest `time_range` first when every copy carries
    one, otherwise input order. Each step's `ghost_id` is what a caller
    passes to ghost_engine.fetch_ghost_copy() to actually pull the payload.
    """
    orderable = all((c.get("time_range") or {}).get("start") for c in ghost_copies)
    ordered = sorted(ghost_copies, key=lambda c: c["time_range"]["start"]) if orderable else list(ghost_copies)

    return {
        "order": "time" if orderable else "input",
        "steps": [
            {
                "sequence": i,
                "ghost_id": c.get("id"),
                "system": c.get("system"),
                "type": c.get("type"),
            }
            for i, c in enumerate(ordered)
        ],
        "total_steps": len(ordered),
    }
