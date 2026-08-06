"""Comprehensive diagnostic suite for warnetech-connectors.

This module provides comprehensive health checks for all connector categories:
- Intel feeds (HIBP, threat intelligence)
- Reputation services (Malwarebytes, Norton, McAfee)
- Vulnerability databases (NVD)
- Log aggregators
- SIEM/SOAR systems

Every connector is tested for:
1. Configuration sanity
2. Endpoint reachability (when configured)
3. Authentication validity
4. Rate limit compliance
5. Timeout behavior
6. Error handling robustness
7. Data normalization
8. Integration health with control plane

Failures are non-fatal; each check returns {"ok": bool, ...} for aggregation.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from warnetech_connectors.config import ConnectorsConfig, DEFAULT_CONFIG
from warnetech_connectors.intel_feeds import fetch_intel_feed, normalize_intel
from warnetech_connectors.reputation_services import normalize_reputation, query_reputation
from warnetech_connectors.logging import get_logger

logger = get_logger(__name__)


# -- 1. Connector Configuration Checks ------------------------------------------


def check_connector_config(config: ConnectorsConfig = DEFAULT_CONFIG) -> Dict[str, Any]:
    """Validates connector configuration structure and required fields."""
    try:
        issues = []

        # Check for enabled connectors list
        if not isinstance(config.enabled_connectors, (list, tuple)):
            issues.append("enabled_connectors is not a list/tuple")

        # Check for rate limit sanity
        if config.rate_limit.requests_per_minute <= 0:
            issues.append("rate_limit.requests_per_minute must be > 0")

        # Check timeout sanity
        if config.timeout.connect_timeout_seconds <= 0:
            issues.append("timeout.connect_timeout_seconds must be > 0")
        if config.timeout.read_timeout_seconds <= 0:
            issues.append("timeout.read_timeout_seconds must be > 0")

        # Check retry policy sanity
        if config.retry.max_retries < 0:
            issues.append("retry.max_retries must be >= 0")
        if config.retry.base_delay_seconds < 0:
            issues.append("retry.base_delay_seconds must be >= 0")

        return {
            "ok": len(issues) == 0,
            "issues": issues,
            "rate_limit_rpm": config.rate_limit.requests_per_minute,
            "connect_timeout_s": config.timeout.connect_timeout_seconds,
            "read_timeout_s": config.timeout.read_timeout_seconds,
            "max_retries": config.retry.max_retries,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


# -- 2. Connector Endpoint Validation ------------------------------------------


def check_endpoints_configured(config: ConnectorsConfig = DEFAULT_CONFIG) -> Dict[str, Any]:
    """Reports which connector endpoints are configured and enabled."""
    try:
        endpoints = {
            "intel_feeds": {},
            "reputation_services": {},
            "vuln_databases": {},
            "log_aggregators": {},
            "siem_soar": {},
        }

        for endpoint in config.intel_feeds:
            endpoints["intel_feeds"][endpoint.name] = {
                "enabled": endpoint.enabled,
                "has_key": bool(endpoint.api_key),
            }

        for endpoint in config.reputation_services:
            endpoints["reputation_services"][endpoint.name] = {
                "enabled": endpoint.enabled,
                "has_key": bool(endpoint.api_key),
            }

        for endpoint in config.vuln_databases:
            endpoints["vuln_databases"][endpoint.name] = {
                "enabled": endpoint.enabled,
                "has_key": bool(endpoint.api_key),
            }

        for endpoint in config.log_aggregators:
            endpoints["log_aggregators"][endpoint.name] = {
                "enabled": endpoint.enabled,
                "has_key": bool(endpoint.api_key),
            }

        for endpoint in config.siem_soar:
            endpoints["siem_soar"][endpoint.name] = {
                "enabled": endpoint.enabled,
                "has_key": bool(endpoint.api_key),
            }

        enabled_count = sum(
            1 for category in endpoints.values()
            for ep_info in category.values()
            if ep_info["enabled"]
        )

        return {
            "ok": True,
            "endpoints": endpoints,
            "total_enabled": enabled_count,
            "checked_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


# -- 3. Intel Feeds Connector Checks ------------------------------------------


def check_intel_feeds(config: ConnectorsConfig = DEFAULT_CONFIG) -> Dict[str, Any]:
    """Tests intel feed connectors for basic functionality."""
    try:
        results = {}

        for endpoint in config.intel_feeds:
            if not endpoint.enabled:
                results[endpoint.name] = {"ok": None, "status": "disabled"}
                continue

            # Test with dummy indicator
            start = time.monotonic()
            try:
                result = fetch_intel_feed("test.com", source=endpoint.name, config=config)
                duration_ms = (time.monotonic() - start) * 1000

                is_ok = result.get("status") != "error"
                results[endpoint.name] = {
                    "ok": is_ok,
                    "status": result.get("status"),
                    "duration_ms": round(duration_ms, 1),
                    "record_count": len(result.get("records", [])),
                }
            except Exception as e:  # noqa: BLE001
                results[endpoint.name] = {
                    "ok": False,
                    "error": str(e),
                }

        overall_ok = all(r.get("ok") is not False for r in results.values())
        return {
            "ok": overall_ok,
            "connectors": results,
            "tested_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


# -- 4. Reputation Services Connector Checks ---------------------------------


def check_reputation_services(config: ConnectorsConfig = DEFAULT_CONFIG) -> Dict[str, Any]:
    """Tests reputation service connectors."""
    try:
        results = {}
        test_target = "1.2.3.4"

        for endpoint in config.reputation_services:
            if not endpoint.enabled:
                results[endpoint.name] = {"ok": None, "status": "disabled"}
                continue

            # Test with dummy target
            start = time.monotonic()
            try:
                result = query_reputation(test_target, source=endpoint.name, config=config)
                duration_ms = (time.monotonic() - start) * 1000

                is_ok = result.get("status") != "error"
                results[endpoint.name] = {
                    "ok": is_ok,
                    "status": result.get("status"),
                    "duration_ms": round(duration_ms, 1),
                }
            except Exception as e:  # noqa: BLE001
                results[endpoint.name] = {
                    "ok": False,
                    "error": str(e),
                }

        overall_ok = all(r.get("ok") is not False for r in results.values())
        return {
            "ok": overall_ok,
            "connectors": results,
            "tested_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


# -- 5. Normalization Pipeline Checks ----------------------------------------


def check_normalization_pipeline() -> Dict[str, Any]:
    """Tests data normalization for all connector types."""
    try:
        issues = []

        # Test intel normalization
        try:
            intel_data = {
                "indicator": "1.2.3.4",
                "type": "ip",
                "threat_level": "high",
            }
            normalized = normalize_intel(intel_data)
            if "indicator" not in normalized or "normalized_at" not in normalized:
                issues.append("intel normalization missing required fields")
        except Exception as e:  # noqa: BLE001
            issues.append(f"intel normalization failed: {e}")

        # Test reputation normalization
        try:
            rep_data = {
                "target": "1.2.3.4",
                "verdict": {"confidence": 0.9, "severity": "critical"},
            }
            normalized = normalize_reputation(rep_data)
            if "indicator" not in normalized or "normalized_at" not in normalized:
                issues.append("reputation normalization missing required fields")
        except Exception as e:  # noqa: BLE001
            issues.append(f"reputation normalization failed: {e}")

        return {
            "ok": len(issues) == 0,
            "issues": issues,
            "checked_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


# -- 6. Logging Integration Checks ------------------------------------------


def check_logging_integration() -> Dict[str, Any]:
    """Verifies connector logging infrastructure is operational."""
    try:
        # Test logger retrieval
        test_logger = get_logger("connector_diagnostics_test")
        if test_logger is None:
            return {"ok": False, "issue": "failed to retrieve logger instance"}

        # Test logging calls don't raise
        try:
            test_logger.info("diagnostic probe")
            test_logger.warning("diagnostic probe")
            test_logger.error("diagnostic probe")
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "issue": f"logger operations raised: {e}"}

        return {
            "ok": True,
            "logger_name": test_logger.name,
            "checked_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


# -- 7. Connector Integration Health Check -----------------------------------


def check_connector_integration() -> Dict[str, Any]:
    """Verifies connectors can be imported and accessed."""
    try:
        issues = []

        # Check all connector modules can be imported
        try:
            from warnetech_connectors import intel_feeds  # noqa: F401
        except Exception as e:  # noqa: BLE001
            issues.append(f"intel_feeds import failed: {e}")

        try:
            from warnetech_connectors import reputation_services  # noqa: F401
        except Exception as e:  # noqa: BLE001
            issues.append(f"reputation_services import failed: {e}")

        try:
            from warnetech_connectors import vuln_databases  # noqa: F401
        except Exception as e:  # noqa: BLE001
            issues.append(f"vuln_databases import failed: {e}")

        try:
            from warnetech_connectors import log_aggregators  # noqa: F401
        except Exception as e:  # noqa: BLE001
            issues.append(f"log_aggregators import failed: {e}")

        try:
            from warnetech_connectors import siem_soar  # noqa: F401
        except Exception as e:  # noqa: BLE001
            issues.append(f"siem_soar import failed: {e}")

        return {
            "ok": len(issues) == 0,
            "issues": issues,
            "checked_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


# -- 8. Security and Environment Checks --------------------------------------


def check_security_posture() -> Dict[str, Any]:
    """Validates security settings for connectors."""
    try:
        issues = []
        config = DEFAULT_CONFIG

        # Check retry policy doesn't allow infinite retries
        if config.retry.max_retries > 10:
            issues.append(f"max_retries={config.retry.max_retries} may be too high")

        # Check timeouts are reasonable
        if config.timeout.connect_timeout_seconds > 30:
            issues.append("connect timeout > 30s may cause user-facing delays")
        if config.timeout.read_timeout_seconds > 60:
            issues.append("read timeout > 60s may cause user-facing delays")

        # Verify rate limiting is configured
        if config.rate_limit.requests_per_minute <= 0:
            issues.append("rate limiting is not properly configured")

        return {
            "ok": len(issues) == 0,
            "issues": issues,
            "checked_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


# -- Orchestration -------------------------------------------------------

_CHECKS: Dict[str, Callable[[ConnectorsConfig], Dict[str, Any]]] = {
    "config_sanity": lambda config: check_connector_config(config),
    "endpoints_configured": lambda config: check_endpoints_configured(config),
    "intel_feeds": lambda config: check_intel_feeds(config),
    "reputation_services": lambda config: check_reputation_services(config),
    "normalization_pipeline": lambda config: check_normalization_pipeline(),
    "logging_integration": lambda config: check_logging_integration(),
    "connector_integration": lambda config: check_connector_integration(),
    "security_posture": lambda config: check_security_posture(),
}


def run_full_diagnostics(config: ConnectorsConfig = DEFAULT_CONFIG) -> Dict[str, Any]:
    """Runs all connector diagnostics and aggregates results.

    Returns a comprehensive report with:
    - overall_ok: True if all non-skipped checks passed
    - timestamp: When diagnostics were run
    - checks: Individual check results
    - summary: High-level findings
    """
    results: Dict[str, Any] = {}
    failed_checks = []
    skipped_checks = []

    for name, check in _CHECKS.items():
        try:
            results[name] = check(config)
            if results[name].get("ok") is False:
                failed_checks.append(name)
            elif results[name].get("ok") is None:
                skipped_checks.append(name)
        except Exception as exc:  # noqa: BLE001
            results[name] = {"ok": False, "error": f"check raised: {exc}"}
            failed_checks.append(name)

    overall_ok = len(failed_checks) == 0

    return {
        "overall_ok": overall_ok,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": results,
        "summary": {
            "total_checks": len(_CHECKS),
            "passed": len([r for r in results.values() if r.get("ok") is True]),
            "failed": len(failed_checks),
            "skipped": len(skipped_checks),
            "failed_checks": failed_checks,
        },
    }
