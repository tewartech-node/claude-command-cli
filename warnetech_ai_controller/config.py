"""Configuration for the Warnetech AI Controller: embedding model settings,
relevance thresholds, recall planning parameters, strategy generation
parameters, and external intel sources.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmbeddingSettings:
    dimensions: int = 768
    model: str = "hash-projection"  # deterministic, dependency-free fallback


@dataclass(frozen=True)
class RelevanceThresholds:
    min_similarity: float = 0.15
    top_k_default: int = 10


@dataclass(frozen=True)
class RecallPlanningParams:
    target_coverage_ratio: float = 0.10
    max_slices: int = 200


@dataclass(frozen=True)
class StrategyParams:
    min_confidence_for_signature_update: float = 0.6
    metrics_weight: float = 0.3
    anomaly_weight: float = 0.4
    intel_weight: float = 0.3


@dataclass(frozen=True)
class ExternalIntelSource:
    name: str
    endpoint: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.endpoint)


def _default_intel_sources() -> tuple[ExternalIntelSource, ...]:
    return (
        ExternalIntelSource(name="malwarebytes", endpoint=os.environ.get("MALWAREBYTES_ENDPOINT", "")),
        ExternalIntelSource(name="have_i_been_pwned", endpoint=os.environ.get("HIBP_ENDPOINT", "")),
        ExternalIntelSource(name="norton", endpoint=os.environ.get("NORTON_ENDPOINT", "")),
        ExternalIntelSource(name="mcafee", endpoint=os.environ.get("MCAFEE_ENDPOINT", "")),
    )


@dataclass(frozen=True)
class AIControllerConfig:
    embedding: EmbeddingSettings = field(default_factory=EmbeddingSettings)
    relevance: RelevanceThresholds = field(default_factory=RelevanceThresholds)
    recall: RecallPlanningParams = field(default_factory=RecallPlanningParams)
    strategy: StrategyParams = field(default_factory=StrategyParams)
    intel_sources: tuple[ExternalIntelSource, ...] = field(default_factory=_default_intel_sources)


DEFAULT_CONFIG = AIControllerConfig()
