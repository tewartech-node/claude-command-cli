"""HTTP endpoints for warnetech-server. Every handler calls into the
appropriate control-plane, database, CLI, or AI integration module — no
handler contains business logic of its own beyond translating between the
HTTP request/response shape and that module's API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from .ai_integration import AIIntegration
from .cli_integration import CLIIntegration
from .config import ServerConfig
from .container_runner import ContainerRunner
from .control_plane_client import ControlPlaneClient
from .database import ServerDatabase
from .middleware import Request, Response
from .security import ValidationError, validate_json_body, validate_string
from .security_intel_integration import SecurityIntelIntegration
from .test_harness import TestHarness
from .utils import now_iso


@dataclass
class ServerDependencies:
    config: ServerConfig
    control_plane: ControlPlaneClient
    database: ServerDatabase
    cli: CLIIntegration
    ai: Optional[AIIntegration]
    test_harness: TestHarness
    security_intel: Optional[SecurityIntelIntegration]


RouteHandler = Callable[[Request, ServerDependencies], Response]


class Router:
    def __init__(self) -> None:
        self._routes: dict[tuple[str, str], RouteHandler] = {}

    def register(self, method: str, path: str, handler: RouteHandler) -> None:
        self._routes[(method.upper(), path)] = handler

    def dispatch(self, req: Request, deps: ServerDependencies) -> Response:
        handler = self._routes.get((req.method.upper(), req.path))
        if handler is None:
            return Response(status=404, body={"error": "not_found", "path": req.path})
        try:
            return handler(req, deps)
        except ValidationError as exc:
            return Response(status=400, body={"error": "invalid_request", "detail": str(exc)})


# -- handlers -----------------------------------------------------------------------


def get_status(req: Request, deps: ServerDependencies) -> Response:
    return Response(status=200, body={
        "server": "warnetech-server",
        "time": now_iso(),
        "control_plane": deps.control_plane.health(),
        "database": deps.database.health(),
        "cli_available": deps.cli.is_available(),
    })


def get_metrics(req: Request, deps: ServerDependencies) -> Response:
    source_id = validate_string(req.query.get("source_id", ""), field="source_id", allow_empty=False)
    metrics = deps.database.read_metrics(source_id)
    return Response(status=200, body={"source_id": source_id, "metrics": metrics})


def get_signatures(req: Request, deps: ServerDependencies) -> Response:
    attack_type = req.query.get("attack_type") or None
    signatures = deps.control_plane.query_signatures(attack_type)
    return Response(status=200, body={"signatures": signatures, "count": len(signatures)})


def post_learn(req: Request, deps: ServerDependencies) -> Response:
    body = validate_json_body(req.json_body or {}, required_fields=("attack_type", "pattern", "true_positive"))
    result = deps.control_plane.trigger_learning(
        body["attack_type"], body["pattern"], body.get("matched_ids", []), bool(body["true_positive"])
    )
    return Response(status=200 if result is not None else 502, body={"result": result})


def post_recover(req: Request, deps: ServerDependencies) -> Response:
    body = validate_json_body(req.json_body or {}, required_fields=("incident_id",))
    result = deps.control_plane.trigger_recovery(body["incident_id"])
    return Response(status=200 if result is not None else 502, body={"result": result})


def post_slice(req: Request, deps: ServerDependencies) -> Response:
    body = validate_json_body(req.json_body or {})
    result = deps.control_plane.slice_operation(body)
    return Response(status=200 if result is not None else 502, body={"result": result})


def post_compress(req: Request, deps: ServerDependencies) -> Response:
    body = validate_json_body(req.json_body or {})
    result = deps.control_plane.compress_operation(body)
    return Response(status=200 if result is not None else 502, body={"result": result})


def post_ghost_create(req: Request, deps: ServerDependencies) -> Response:
    body = validate_json_body(req.json_body or {})
    result = deps.control_plane.ghost_create(body)
    return Response(status=200 if result is not None else 502, body={"result": result})


def post_ghost_recall(req: Request, deps: ServerDependencies) -> Response:
    body = validate_json_body(req.json_body or {}, required_fields=("query",))
    result = deps.control_plane.ghost_recall(body)
    return Response(status=200 if result is not None else 502, body={"result": result})


def post_retention_apply(req: Request, deps: ServerDependencies) -> Response:
    body = validate_json_body(req.json_body or {})
    result = deps.control_plane.update_retention_policy(body)
    return Response(status=200 if result is not None else 502, body={"result": result})


def get_retention_policy(req: Request, deps: ServerDependencies) -> Response:
    result = deps.control_plane.get_retention_policy()
    return Response(status=200 if result is not None else 502, body={"policy": result})


def post_ai_query(req: Request, deps: ServerDependencies) -> Response:
    if deps.ai is None:
        return Response(status=503, body={"error": "ai_integration_unavailable"})
    body = validate_json_body(req.json_body or {})
    mode = body.get("mode", "search")
    if mode == "strategy":
        result = deps.ai.assisted_defense_strategy(body.get("available_slices", []), body.get("total_data_size", 0))
    else:
        query_text = validate_string(body.get("query", ""), field="query")
        result = deps.ai.send_query(query_text, body.get("slice_embeddings", []))
    return Response(status=200, body={"mode": mode, "result": result})


def post_ai_recall(req: Request, deps: ServerDependencies) -> Response:
    if deps.ai is None:
        return Response(status=503, body={"error": "ai_integration_unavailable"})
    body = validate_json_body(req.json_body or {}, required_fields=("available_slices", "total_data_size"))
    plan = deps.ai.recall_plan(body["available_slices"], body["total_data_size"], body.get("query_params"))
    return Response(status=200, body={"plan": plan})


def post_tests_run(req: Request, deps: ServerDependencies) -> Response:
    body = validate_json_body(req.json_body or {}, required_fields=("name", "kind", "container_profile"))
    scenario = deps.test_harness.define_scenario(
        name=body["name"], kind=body["kind"], container_profile=body["container_profile"], payloads=body.get("payloads", []),
    )
    result = deps.test_harness.run_scenario(scenario)
    return Response(status=200, body={"scenario": scenario.to_dict(), "result": result.to_dict()})


def get_tests_results(req: Request, deps: ServerDependencies) -> Response:
    test_id = req.query.get("test_id") or None
    results = deps.test_harness.query_results(test_id=test_id)
    return Response(status=200, body={"results": results, "count": len(results)})


def get_db_health(req: Request, deps: ServerDependencies) -> Response:
    return Response(status=200, body=deps.database.health())


def post_db_sync(req: Request, deps: ServerDependencies) -> Response:
    partitions_ok = deps.database.sync_partitions()
    rollups_ok = deps.database.refresh_rollups()
    ok = partitions_ok and rollups_ok
    return Response(status=200 if ok else 502, body={"partitions_synced": partitions_ok, "rollups_refreshed": rollups_ok})


def build_router() -> Router:
    router = Router()
    router.register("GET", "/status", get_status)
    router.register("GET", "/metrics", get_metrics)
    router.register("GET", "/signatures", get_signatures)
    router.register("POST", "/learn", post_learn)
    router.register("POST", "/recover", post_recover)
    router.register("POST", "/slice", post_slice)
    router.register("POST", "/compress", post_compress)
    router.register("POST", "/ghost/create", post_ghost_create)
    router.register("POST", "/ghost/recall", post_ghost_recall)
    router.register("POST", "/retention/apply", post_retention_apply)
    router.register("GET", "/retention/policy", get_retention_policy)
    router.register("POST", "/ai/query", post_ai_query)
    router.register("POST", "/ai/recall", post_ai_recall)
    router.register("POST", "/tests/run", post_tests_run)
    router.register("GET", "/tests/results", get_tests_results)
    router.register("GET", "/db/health", get_db_health)
    router.register("POST", "/db/sync", post_db_sync)
    return router
