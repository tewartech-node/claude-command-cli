"""Integration of external security intelligence feeds: merging,
relevance ranking, and summarization.

Operates on whatever intel records the caller has already fetched from
`warnetech_server.config.SecurityConnectors`-configured endpoints
(Malwarebytes, HIBP, Norton, McAfee) — this module has no network access of
its own; fetching is the caller's job, this is purely the merge/rank/summarize
layer over already-retrieved records.
"""

from __future__ import annotations

from .config import AIControllerConfig, DEFAULT_CONFIG
from .utils import now_iso


def merge_intel(intel: list[dict]) -> list[dict]:
    """Deduplicates intel records by (source, indicator), keeping the
    highest-confidence record when the same indicator appears from
    multiple feeds.
    """
    best: dict[tuple, dict] = {}
    for record in intel:
        key = (record.get("indicator"), record.get("indicator_type"))
        existing = best.get(key)
        if existing is None or record.get("confidence", 0) > existing.get("confidence", 0):
            best[key] = record
    return list(best.values())


def rank_intel_relevance(intel: list[dict], config: AIControllerConfig = DEFAULT_CONFIG) -> list[dict]:
    enabled_sources = {s.name for s in config.intel_sources if s.enabled}

    def score(record: dict) -> float:
        confidence = record.get("confidence", 0.0)
        source_bonus = 0.1 if record.get("source") in enabled_sources else 0.0
        severity_bonus = {"critical": 0.3, "high": 0.2, "medium": 0.1}.get(record.get("severity", ""), 0.0)
        return min(1.0, confidence + source_bonus + severity_bonus)

    ranked = [{**record, "relevance_score": score(record)} for record in intel]
    ranked.sort(key=lambda r: r["relevance_score"], reverse=True)
    return ranked


def produce_intel_summary(intel: list[dict]) -> dict:
    merged = merge_intel(intel)
    by_source: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for record in merged:
        source = record.get("source", "unknown")
        severity = record.get("severity", "unknown")
        by_source[source] = by_source.get(source, 0) + 1
        by_severity[severity] = by_severity.get(severity, 0) + 1

    return {
        "total_records": len(merged),
        "raw_record_count": len(intel),
        "duplicates_removed": len(intel) - len(merged),
        "by_source": by_source,
        "by_severity": by_severity,
        "summarized_at": now_iso(),
    }
