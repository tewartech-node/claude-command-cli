"""Interactions with warnetech-project-supabase over the PostgREST Data API.

Uses only the standard library (``urllib``) so the package has no required
third-party dependency for its most critical I/O path. Every method fails
soft: on network error or non-2xx response it logs and returns an empty/None
result rather than raising, consistent with the control plane's invariant
that the threat-block path must never depend on Postgres being reachable.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Optional

from .config import ControlPlaneConfig, DEFAULT_CONFIG
from .logging import get_logger

logger = get_logger(__name__)


class SupabaseDatabase:
    def __init__(self, config: ControlPlaneConfig = DEFAULT_CONFIG) -> None:
        self._config = config

    @property
    def _available(self) -> bool:
        return bool(self._config.supabase_url and self._config.supabase_key)

    def _request(self, method: str, path: str, body: Optional[Any] = None, params: Optional[dict] = None) -> Any:
        if not self._available:
            logger.warning("supabase not configured; request skipped", path=path)
            return None

        url = f"{self._config.supabase_url.rstrip('/')}/rest/v1/{path.lstrip('/')}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"

        data = json.dumps(body, default=str).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("apikey", self._config.supabase_key)
        req.add_header("Authorization", f"Bearer {self._config.supabase_key}")
        req.add_header("Content-Type", "application/json")
        if method in ("POST", "PATCH"):
            req.add_header("Prefer", "return=representation")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            logger.error("supabase http error", path=path, status=exc.code, body=exc.read().decode(errors="replace"))
            return None
        except urllib.error.URLError as exc:
            logger.error("supabase unreachable", path=path, reason=str(exc.reason))
            return None

    # -- reads ------------------------------------------------------------

    def read_signatures(self, limit: int = 5000) -> list[dict]:
        result = self._request("GET", "signatures", params={"select": "*", "limit": limit})
        return result or []

    def read_anomalies(self, status: str = "open", limit: int = 500) -> list[dict]:
        result = self._request("GET", "anomalies", params={"select": "*", "status": f"eq.{status}", "limit": limit})
        return result or []

    # -- writes -------------------------------------------------------------

    def write_metrics(self, rollups: list[dict]) -> bool:
        if not rollups:
            return True
        result = self._request("POST", "metric_rollups", body=rollups)
        ok = result is not None
        logger.info("metrics written", count=len(rollups), ok=ok)
        return ok

    def store_anomaly(self, anomaly: dict) -> Optional[dict]:
        result = self._request("POST", "anomalies", body=[anomaly])
        return result[0] if result else None

    def upsert_signature(self, signature: dict) -> Optional[dict]:
        result = self._request(
            "POST", "signatures", body=[signature], params={"on_conflict": "id"}
        )
        return result[0] if result else None

    # -- RPC (complex analytics run as Postgres functions) -------------------

    def call_rpc(self, function_name: str, args: dict) -> Any:
        return self._request("POST", f"rpc/{function_name}", body=args)

    def sync_partitions(self) -> bool:
        """Invokes the server-side partition-maintenance function so this
        process never needs raw DDL privileges.
        """
        result = self.call_rpc("maintain_partitions", {})
        ok = result is not None
        logger.info("partition sync requested", ok=ok)
        return ok

    def sync_threat_event_partitions(self) -> bool:
        """Invokes maintain_threat_event_partitions() — dedicated
        threat_events partition maintenance, redundant with (not a
        replacement for) sync_partitions()'s own threat_events coverage.
        Both are idempotent create-if-missing operations; calling both is
        harmless, just double work.
        """
        result = self.call_rpc("maintain_threat_event_partitions", {})
        ok = result is not None
        logger.info("threat_events partition sync requested", ok=ok)
        return ok
