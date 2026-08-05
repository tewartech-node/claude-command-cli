"""Connectors for log aggregation platforms: pushing local logs out and
pulling external logs in.
"""

from __future__ import annotations

import time

from .config import ConnectorsConfig, DEFAULT_CONFIG
from .logging import get_logger, log_error, log_request, log_response
from .utils import now_iso, request_with_retry

logger = get_logger(__name__)


def push_logs(source: str, logs: list[dict], config: ConnectorsConfig = DEFAULT_CONFIG) -> dict:
    endpoint = config.find(source)
    if endpoint is None or not config.is_enabled(source):
        return {"source": source, "status": "disabled", "pushed": 0}

    log_request(logger, source, "POST", endpoint.endpoint)
    start = time.monotonic()
    headers = {"Authorization": f"Bearer {endpoint.api_key}"} if endpoint.api_key else {}
    result = request_with_retry(
        "POST", endpoint.endpoint, headers=headers, body={"logs": logs},
        timeout=config.timeout.read_timeout_seconds,
        max_retries=config.retry.max_retries,
        base_delay_seconds=config.retry.base_delay_seconds,
        max_delay_seconds=config.retry.max_delay_seconds,
    )
    duration_ms = (time.monotonic() - start) * 1000
    log_response(logger, source, result.ok, duration_ms, result.status)

    if not result.ok:
        log_error(logger, source, result.error or "unknown error")
        return {"source": source, "status": "error", "error": result.error, "pushed": 0}

    return {"source": source, "status": "ok", "pushed": len(logs), "pushed_at": now_iso()}


def pull_logs(source: str, query: dict, config: ConnectorsConfig = DEFAULT_CONFIG) -> dict:
    endpoint = config.find(source)
    if endpoint is None or not config.is_enabled(source):
        return {"source": source, "status": "disabled", "records": []}

    log_request(logger, source, "POST", endpoint.endpoint)
    start = time.monotonic()
    headers = {"Authorization": f"Bearer {endpoint.api_key}"} if endpoint.api_key else {}
    result = request_with_retry(
        "POST", f"{endpoint.endpoint.rstrip('/')}/query", headers=headers, body=query,
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
    return {"source": source, "status": "ok", "records": records, "pulled_at": now_iso()}


def normalize_logs(data: list[dict]) -> list[dict]:
    normalized = []
    for entry in data:
        normalized.append({
            "message": entry.get("message") or entry.get("msg", ""),
            "level": entry.get("level", "info"),
            "source": entry.get("source", "unknown"),
            "timestamp": entry.get("timestamp") or entry.get("time") or now_iso(),
            "raw": entry,
        })
    return normalized
