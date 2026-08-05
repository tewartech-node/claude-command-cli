"""Connectors for threat intelligence feeds.

Every function returns plain JSON-serializable dicts and never mutates
production data directly — `push_intel_to_control_plane` accepts a `sink`
callable the caller supplies (e.g. warnetech_control_plane's anomaly
buffer) rather than reaching into control-plane internals itself. With no
sink, it returns the formatted payload without delivering it anywhere, so
this module stays testable and decoupled from the control plane's shape.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

from .config import ConnectorsConfig, DEFAULT_CONFIG
from .logging import get_logger, log_error, log_push_to_control_plane, log_request, log_response
from .utils import now_iso, request_with_retry

logger = get_logger(__name__)


def fetch_intel_feed(source: str, config: ConnectorsConfig = DEFAULT_CONFIG) -> dict:
    endpoint = config.find(source)
    if endpoint is None or not config.is_enabled(source):
        return {"source": source, "status": "disabled", "records": []}

    log_request(logger, source, "GET", endpoint.endpoint)
    start = time.monotonic()
    headers = {"Authorization": f"Bearer {endpoint.api_key}"} if endpoint.api_key else {}
    result = request_with_retry(
        "GET", endpoint.endpoint, headers=headers,
        timeout=config.timeout.read_timeout_seconds,
        max_retries=config.retry.max_retries,
        base_delay_seconds=config.retry.base_delay_seconds,
        max_delay_seconds=config.retry.max_delay_seconds,
    )
    duration_ms = (time.monotonic() - start) * 1000
    log_response(logger, source, result.ok, duration_ms, result.status)

    if not result.ok:
        log_error(logger, source, result.error or "unknown error")
        return {"source": source, "status": "error", "error": result.error, "records": []}

    records = result.body if isinstance(result.body, list) else [result.body] if result.body else []
    return {"source": source, "status": "ok", "records": records, "fetched_at": now_iso()}


def normalize_intel(data: dict) -> dict:
    """Maps a raw feed record onto the common intel shape consumed by
    warnetech_ai_controller.security_intel: indicator, indicator_type,
    source, confidence, severity.
    """
    return {
        "indicator": data.get("indicator") or data.get("ioc") or data.get("value"),
        "indicator_type": data.get("indicator_type") or data.get("type", "unknown"),
        "source": data.get("source", "intel_feed"),
        "confidence": float(data.get("confidence", 0.5)),
        "severity": data.get("severity", "medium"),
        "raw": data,
        "normalized_at": now_iso(),
    }


def push_intel_to_control_plane(data: list[dict], sink: Optional[Callable[[list[dict]], int]] = None) -> dict:
    normalized = [d if d.get("normalized_at") else normalize_intel(d) for d in data]
    delivered = sink(normalized) if sink is not None else 0
    log_push_to_control_plane(logger, "intel_feeds", delivered)
    return {"total": len(normalized), "delivered": delivered, "pushed_at": now_iso()}
