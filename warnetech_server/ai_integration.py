"""Integration with AI systems: sending queries to AI controllers,
receiving slice relevance and recall plans, coordinating AI-driven
reconstruction of datasets, and managing AI-assisted defense strategies.

Wraps the real `AIController` in `warnetech_cli/ai_controller.py`, already
present in this repository, rather than reimplementing slice selection or
semantic search — see that module for the actual reconstruction math this
class delegates to.

`ai_controller.py` is loaded directly by file path rather than via
`import warnetech_cli.ai_controller`. The latter would execute
`warnetech_cli/__init__.py` first, which pulls in the full CLI package
(command parsing, `SecurityManager`, `cryptography`) just to reach one
pure-stdlib helper class — heavy, unnecessary coupling for a server-side
integration point, and a single point of failure if any of that package's
other dependencies are unavailable. Loading the module file directly keeps
this integration exactly as resilient as `ai_controller.py` itself.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Optional

from .logging import get_logger, log_ai_interaction

logger = get_logger(__name__)


def _load_ai_controller_class():
    module_path = Path(__file__).resolve().parent.parent / "warnetech_cli" / "ai_controller.py"
    if not module_path.exists():
        raise RuntimeError(f"warnetech_cli/ai_controller.py not found at {module_path}")

    spec = importlib.util.spec_from_file_location("warnetech_cli._ai_controller_standalone", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load module spec for {module_path}")

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 - surface any load-time failure clearly
        raise RuntimeError(f"failed to load {module_path}: {exc}") from exc

    return module.AIController


class AIIntegration:
    def __init__(self) -> None:
        AIController = _load_ai_controller_class()
        self._controller = AIController

    # -- queries --------------------------------------------------------------------

    def send_query(self, query_text: str, slice_embeddings: list[dict]) -> list[dict]:
        results = self._controller.semantic_search(query_text, slice_embeddings)
        log_ai_interaction(logger, "query", True, {"query_length": len(query_text), "result_count": len(results)})
        return results

    # -- recall plans -------------------------------------------------------------------

    def recall_plan(self, available_slices: list[dict], total_data_size: int, query_params: Optional[dict] = None) -> dict:
        plan = self._controller.select_optimal_slices(available_slices, total_data_size, query_params)
        log_ai_interaction(logger, "recall_plan", True, {"selected": plan.get("selected_slice_count", 0)})
        return plan

    # -- reconstruction --------------------------------------------------------------------

    def coordinate_reconstruction(self, selected_slices: list[dict], original_size: int) -> dict:
        result = self._controller.reconstruct_data(selected_slices, original_size)
        log_ai_interaction(logger, "reconstruction", True, {"status": result.get("reconstruction_status")})
        return result

    def generate_embedding(self, data: bytes, dims: int = 768) -> list[float]:
        return self._controller.generate_embeddings(data, dims)

    # -- AI-assisted defense strategy ------------------------------------------------------

    def assisted_defense_strategy(self, available_slices: list[dict], total_data_size: int) -> dict[str, Any]:
        """Combines importance analysis and a success prediction into one
        recommendation, used by routes.ai_query() when the caller asks for
        a strategy rather than a raw recall plan.
        """
        importance = self._controller.analyze_slice_importance(available_slices)
        plan = self.recall_plan(available_slices, total_data_size)
        prediction = self._controller.predict_reconstruction_success(plan.get("slices", []), total_data_size)

        strategy = {
            "importance": importance,
            "recall_plan": plan,
            "prediction": prediction,
            "recommendation": prediction.get("recommendation", "acquire_more_slices"),
        }
        log_ai_interaction(logger, "assisted_defense_strategy", True, {"recommendation": strategy["recommendation"]})
        return strategy
