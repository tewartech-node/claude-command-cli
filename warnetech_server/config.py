"""Configuration for warnetech-server: host/port, database connection,
control-plane endpoint, retention/compression defaults, test-harness
settings, and external security service connectors.

warnetech-control-plane is treated as an external service reached over
HTTP (see ARCHITECTURE.md's "Warnetwork Control Plane" entry under Layer 3
external services), not an in-process import — control_plane_client.py
speaks to it purely over `control_plane_url`, so this server has no
dependency on the control plane's own package or its language.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DatabaseSettings:
    supabase_url: str = field(default_factory=lambda: os.environ.get("SUPABASE_URL", ""))
    supabase_key: str = field(default_factory=lambda: os.environ.get("SUPABASE_KEY", ""))
    request_timeout_seconds: int = 10


@dataclass(frozen=True)
class ControlPlaneSettings:
    base_url: str = field(default_factory=lambda: os.environ.get("WARNETECH_CONTROL_PLANE_URL", "http://localhost:8788"))
    api_key: str = field(default_factory=lambda: os.environ.get("WARNETECH_CONTROL_PLANE_KEY", ""))
    timeout_seconds: int = 10


@dataclass(frozen=True)
class RetentionDefaults:
    hot_tier_hours: int = 24
    warm_tier_days: int = 30
    ghost_tier_days: int = 365
    downsample_factor: int = 10


@dataclass(frozen=True)
class CompressionDefaults:
    algorithm: str = "gzip"
    level: int = 6


@dataclass(frozen=True)
class TestHarnessSettings:
    container_image_allowlist: tuple[str, ...] = ("warnetech/attack-sim:latest", "warnetech/defense-sim:latest")
    max_concurrent_containers: int = 4
    container_memory_limit_mb: int = 256
    container_cpu_limit: float = 1.0
    container_network_mode: str = "none"  # isolation: no network by default
    test_timeout_seconds: int = 120


@dataclass(frozen=True)
class SecurityConnectors:
    """Names/endpoints only — never credentials. Each is optional; an empty
    string means the connector is not configured.
    """

    malwarebytes_endpoint: str = field(default_factory=lambda: os.environ.get("MALWAREBYTES_ENDPOINT", ""))
    have_i_been_pwned_endpoint: str = field(default_factory=lambda: os.environ.get("HIBP_ENDPOINT", ""))
    norton_endpoint: str = field(default_factory=lambda: os.environ.get("NORTON_ENDPOINT", ""))
    mcafee_endpoint: str = field(default_factory=lambda: os.environ.get("MCAFEE_ENDPOINT", ""))


@dataclass(frozen=True)
class RateLimitSettings:
    requests_per_minute: int = 120
    burst: int = 20


@dataclass(frozen=True)
class ServerConfig:
    host: str = field(default_factory=lambda: os.environ.get("WARNETECH_SERVER_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.environ.get("WARNETECH_SERVER_PORT", "8080")))

    api_key: str = field(default_factory=lambda: os.environ.get("API_KEY", ""))
    auth_token_secret: str = field(default_factory=lambda: os.environ.get("WARNETECH_AUTH_SECRET", ""))

    cli_entrypoint: str = field(default_factory=lambda: os.environ.get("WARNETECH_CLI_ENTRYPOINT", "termux-cli/warnet"))
    cli_timeout_seconds: int = 30

    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    control_plane: ControlPlaneSettings = field(default_factory=ControlPlaneSettings)
    retention: RetentionDefaults = field(default_factory=RetentionDefaults)
    compression: CompressionDefaults = field(default_factory=CompressionDefaults)
    test_harness: TestHarnessSettings = field(default_factory=TestHarnessSettings)
    security_connectors: SecurityConnectors = field(default_factory=SecurityConnectors)
    rate_limit: RateLimitSettings = field(default_factory=RateLimitSettings)


DEFAULT_CONFIG = ServerConfig()
