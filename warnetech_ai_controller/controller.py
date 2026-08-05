"""Main AI controller interface used by warnetech-server.

Every function here is a thin composition over the specialized modules
(embeddings, relevance, recall_planner, strategy_engine, anomaly_classifier,
test_analyzer, security_intel) — this module owns no logic of its own
beyond wiring inputs to the right submodule and shaping the combined
output. Every function returns a plain, JSON-serializable dict.
"""

from __future__ import annotations

from typing import Optional

from . import anomaly_classifier, recall_planner, relevance, security_intel, strategy_engine, test_analyzer
from .config import AIControllerConfig, DEFAULT_CONFIG
from .embeddings import generate_slice_embedding
from .utils import now_iso


def rank_slices(metadata_list: list[dict], config: AIControllerConfig = DEFAULT_CONFIG) -> dict:
    """Ranks slices by importance (proportional share of total stored size)
    without requiring an external query — useful for retention/ghost-tier
    decisions where "what matters most" is a property of the slices
    themselves, not a search request.
    """
    total_size = sum(s.get("size_bytes", 0) for s in metadata_list)

    ranked = []
    for entry in metadata_list:
        size = entry.get("size_bytes", 0)
        importance = (size / total_size) if total_size else 0.0
        ranked.append({
            **entry,
            "importance": importance,
            "embedding_dims": config.embedding.dimensions,
        })
    ranked.sort(key=lambda e: e["importance"], reverse=True)

    return {
        "total_slices": len(metadata_list),
        "total_size": total_size,
        "ranked": ranked,
        "ranked_at": now_iso(),
    }


_PLAN_RECALL_HOUSEKEEPING_KEYS = ("available_slices", "total_data_size", "query_embedding")


def plan_recall(query: dict, config: AIControllerConfig = DEFAULT_CONFIG) -> dict:
    """`query` carries `available_slices` (list of slice metadata dicts,
    each optionally with an `embedding`), `total_data_size`, and either a
    `query_embedding` (for similarity ranking) or plain fields to match by
    metadata (domain, system, category, time_start/time_end).
    """
    available_slices = query.get("available_slices", [])
    query_embedding = query.get("query_embedding")
    match_fields = {k: v for k, v in query.items() if k not in _PLAN_RECALL_HOUSEKEEPING_KEYS}

    if query_embedding:
        ranked = relevance.rank_by_similarity(query_embedding, available_slices, config)
    elif match_fields:
        ranked = relevance.rank_by_metadata(match_fields, available_slices)
    else:
        # No filter signal at all: rank by size descending so plan_recall
        # still has candidates to select from, largest first.
        ranked = sorted(available_slices, key=lambda s: s.get("size_bytes", 0), reverse=True)

    plan = recall_planner.plan_recall(query, ranked, config)
    plan["recall_map"] = recall_planner.produce_recall_map(plan["slices"])
    return plan


def suggest_signatures(anomalies: list[dict], config: AIControllerConfig = DEFAULT_CONFIG) -> dict:
    recommendations = strategy_engine.suggest_signature_updates(anomalies, config)
    return {
        "recommendation_count": len(recommendations),
        "recommendations": recommendations,
        "generated_at": now_iso(),
    }


def suggest_defense_strategy(metrics: dict, anomalies: list[dict], config: AIControllerConfig = DEFAULT_CONFIG) -> dict:
    return strategy_engine.suggest_defense_strategy(metrics, anomalies, intel=None, config=config)


def classify_anomaly(event: dict) -> dict:
    return anomaly_classifier.explain_classification(event)


def analyze_test_results(results: list[dict]) -> dict:
    return {
        "summary": test_analyzer.summarize_test_results(results),
        "failures": test_analyzer.identify_failures(results),
        "recommendations": test_analyzer.recommend_improvements(results),
    }


def integrate_external_intel(intel: list[dict], config: AIControllerConfig = DEFAULT_CONFIG) -> dict:
    merged = security_intel.merge_intel(intel)
    ranked = security_intel.rank_intel_relevance(merged, config)
    summary = security_intel.produce_intel_summary(intel)
    return {
        "summary": summary,
        "ranked_intel": ranked,
    }
