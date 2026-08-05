"""Retention policies for hot, warm, and ghost tiers: downsampling,
compression, and deletion rules.

Tiers age data down rather than dropping it outright:

    hot (raw, `retention.hot_tier_hours`)
      -> warm (downsampled `retention.downsample_factor`:1, gzip'd, `retention.warm_tier_days`)
      -> ghost (aggregates only, kept `retention.ghost_tier_days`)
      -> deleted

Each transition is a pure function over a list of records so it can be
tested without a clock or real storage.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from .config import ControlPlaneConfig, DEFAULT_CONFIG
from .logging import get_logger
from .utils import gzip_bytes, to_ndjson

logger = get_logger(__name__)


@dataclass(frozen=True)
class TierResult:
    tier: str
    records_in: int
    records_out: int
    bytes_out: int


class RetentionEngine:
    def __init__(self, config: ControlPlaneConfig = DEFAULT_CONFIG) -> None:
        self._config = config

    def is_past_hot_tier(self, record_epoch_seconds: float, now: float | None = None) -> bool:
        now = now if now is not None else time.time()
        age_hours = (now - record_epoch_seconds) / 3600
        return age_hours >= self._config.retention.hot_tier_hours

    def is_past_warm_tier(self, record_epoch_seconds: float, now: float | None = None) -> bool:
        now = now if now is not None else time.time()
        age_days = (now - record_epoch_seconds) / 86400
        return age_days >= self._config.retention.warm_tier_days

    def is_past_ghost_tier(self, record_epoch_seconds: float, now: float | None = None) -> bool:
        now = now if now is not None else time.time()
        age_days = (now - record_epoch_seconds) / 86400
        return age_days >= self._config.retention.ghost_tier_days

    def downsample(self, records: list[dict]) -> list[dict]:
        """Keeps every Nth record, per `retention.downsample_factor`."""
        factor = max(1, self._config.retention.downsample_factor)
        return records[::factor]

    def apply_warm_tier(self, hot_records: list[dict]) -> TierResult:
        downsampled = self.downsample(hot_records)
        body = gzip_bytes(to_ndjson(downsampled).encode("utf-8"), level=self._config.compression.level)
        logger.info("warm tier applied", records_in=len(hot_records), records_out=len(downsampled), bytes_out=len(body))
        return TierResult(tier="warm", records_in=len(hot_records), records_out=len(downsampled), bytes_out=len(body))

    def apply_ghost_tier(self, warm_records: list[dict], aggregate_fn) -> TierResult:
        """`aggregate_fn` collapses warm records into ghost-tier aggregates
        (typically metrics_engine's rollup math). Ghost tier stores only
        aggregates — no per-event detail survives past this point except
        what ghost_engine explicitly preserves as a ghost copy.
        """
        aggregates = aggregate_fn(warm_records)
        body = gzip_bytes(to_ndjson(aggregates).encode("utf-8"), level=self._config.compression.level)
        logger.info("ghost tier applied", records_in=len(warm_records), records_out=len(aggregates), bytes_out=len(body))
        return TierResult(tier="ghost", records_in=len(warm_records), records_out=len(aggregates), bytes_out=len(body))

    def enforce_deletion(self, records: list[dict], epoch_key: str = "epoch_seconds", now: float | None = None) -> list[dict]:
        """Returns only the records that are still within the ghost-tier
        retention window; everything older is dropped.
        """
        now = now if now is not None else time.time()
        kept = [r for r in records if not self.is_past_ghost_tier(r.get(epoch_key, now), now)]
        dropped = len(records) - len(kept)
        if dropped:
            logger.info("retention deletion enforced", dropped=dropped, kept=len(kept))
        return kept
