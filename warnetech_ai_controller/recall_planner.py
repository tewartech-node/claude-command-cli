"""Reconstruction planning: given a query, determines the minimal set of
slices needed to satisfy it.
"""

from __future__ import annotations

from typing import Any

from .config import AIControllerConfig, DEFAULT_CONFIG
from .utils import now_iso


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
