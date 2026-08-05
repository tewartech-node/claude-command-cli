"""Client for warnetech-control-plane: signature queries, scoring requests,
learning triggers, recovery triggers, retention policy updates, and slice
and ghost operations.

warnetech-control-plane is an external service reached over HTTP (per
ARCHITECTURE.md's Layer 3 "Warnetwork Control Plane" entry) — this client
holds no assumptions about its implementation language or process, only
its HTTP contract. Every call fails soft: on error it logs and returns
None, and callers (routes.py) turn that into a degraded-but-honest API
response rather than a 500, matching the invariant that a control-plane
outage must never take the whole server down.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Optional

from .config import ServerConfig
from .logging import get_logger, log_control_plane_call

logger = get_logger(__name__)


class ControlPlaneClient:
    def __init__(self, config: ServerConfig) -> None:
        self._config = config

    def _request(self, method: str, path: str, body: Optional[Any] = None) -> Any:
        url = f"{self._config.control_plane.base_url.rstrip('/')}/{path.lstrip('/')}"
        data = json.dumps(body, default=str).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if self._config.control_plane.api_key:
            req.add_header("Authorization", f"Bearer {self._config.control_plane.api_key}")

        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=self._config.control_plane.timeout_seconds) as resp:
                raw = resp.read()
                result = json.loads(raw) if raw else None
                log_control_plane_call(logger, path, True, (time.monotonic() - start) * 1000)
                return result
        except urllib.error.HTTPError as exc:
            logger.error("control-plane http error", path=path, status=exc.code, body=exc.read().decode(errors="replace"))
        except urllib.error.URLError as exc:
            logger.error("control-plane unreachable", path=path, reason=str(exc.reason))
        log_control_plane_call(logger, path, False, (time.monotonic() - start) * 1000)
        return None

    # -- signatures / scoring -----------------------------------------------------

    def query_signatures(self, attack_type: Optional[str] = None) -> list[dict]:
        path = "signatures" if not attack_type else f"signatures?attack_type={attack_type}"
        result = self._request("GET", path)
        return result or []

    def request_score(self, payload: dict) -> Optional[dict]:
        return self._request("POST", "score", body=payload)

    # -- learning / recovery ----------------------------------------------------------

    def trigger_learning(self, attack_type: str, pattern: str, matched_ids: list[str], true_positive: bool) -> Optional[dict]:
        return self._request(
            "POST", "learn",
            body={"attack_type": attack_type, "pattern": pattern, "matched_ids": matched_ids, "true_positive": true_positive},
        )

    def trigger_recovery(self, incident_id: str) -> Optional[dict]:
        return self._request("POST", "recover", body={"incident_id": incident_id})

    # -- retention -------------------------------------------------------------------

    def update_retention_policy(self, policy: dict) -> Optional[dict]:
        return self._request("POST", "retention/apply", body=policy)

    def get_retention_policy(self) -> Optional[dict]:
        return self._request("GET", "retention/policy")

    # -- slice / ghost -----------------------------------------------------------------

    def slice_operation(self, params: dict) -> Optional[dict]:
        return self._request("POST", "slice", body=params)

    def compress_operation(self, params: dict) -> Optional[dict]:
        return self._request("POST", "compress", body=params)

    def ghost_create(self, params: dict) -> Optional[dict]:
        return self._request("POST", "ghost/create", body=params)

    def ghost_recall(self, params: dict) -> Optional[dict]:
        return self._request("POST", "ghost/recall", body=params)

    def health(self) -> dict:
        result = self._request("GET", "status")
        return {"reachable": result is not None, "detail": result}
