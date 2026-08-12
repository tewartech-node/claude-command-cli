"""
Cost Optimization

Route tasks to free agents first, intelligently fallback to paid if needed.
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CostOptimizedExecutor:
    """Route tasks to free agents, fallback to paid intelligently"""

    def __init__(self, budget_limit: float = 0.0):
        """Initialize with budget limit (0 = free only)"""
        self.budget_limit = budget_limit
        self.cost_so_far = 0.0
        self.execution_log = []

    async def execute(self, task: Dict, **kwargs) -> Dict:
        """
        Execute task with cost-optimized routing

        Priority chain:
        1. Local free agents (Ollama) - $0
        2. Free API tier agents (Groq, HF) - $0
        3. Batch processing during off-peak - $0-1
        4. Paid agents if budget allows
        """

        logger.info(f"Executing task: {task.get('type', 'general')}")

        # Try local agents first
        local_result = await self._try_local_execution(task, **kwargs)
        if local_result and local_result.get("quality_score", 0) > 0.7:
            self.execution_log.append({"stage": "local", "success": True})
            return local_result

        # Try free API agents
        free_result = await self._try_free_api_execution(task, **kwargs)
        if free_result and free_result.get("quality_score", 0) > 0.7:
            self.execution_log.append({"stage": "free_api", "success": True})
            return free_result

        # If within budget, try paid
        if self.budget_limit > 0 and self.cost_so_far < self.budget_limit:
            paid_result = await self._try_paid_execution(task, **kwargs)
            if paid_result:
                cost = paid_result.get("cost", 0)
                if cost <= (self.budget_limit - self.cost_so_far):
                    self.cost_so_far += cost
                    self.execution_log.append({"stage": "paid", "success": True, "cost": cost})
                    return paid_result

        # Last resort: return best available result
        logger.warning(f"Task execution exhausted options")
        return {"success": False, "error": "All execution strategies exhausted"}

    async def _try_local_execution(self, task: Dict, **kwargs) -> Optional[Dict]:
        """Try execution on local Ollama agents"""
        try:
            from .free_agent_pool import FreeAgentPool

            pool = FreeAgentPool()
            result = await pool.execute_with_fallback(
                task.get("prompt", ""),
                task_type=task.get("type", "general"),
                latency_requirement="realtime",
                **kwargs
            )

            if result.success:
                return {
                    "success": True,
                    "output": result.output,
                    "quality_score": result.quality_score,
                    "cost": 0.0,
                }
            return None

        except Exception as e:
            logger.debug(f"Local execution failed: {e}")
            return None

    async def _try_free_api_execution(self, task: Dict, **kwargs) -> Optional[Dict]:
        """Try execution on free API agents"""
        try:
            from .free_agent_pool import FreeAgentPool

            pool = FreeAgentPool()
            result = await pool.execute_with_fallback(
                task.get("prompt", ""),
                task_type=task.get("type", "general"),
                latency_requirement="normal",
                **kwargs
            )

            if result.success:
                return {
                    "success": True,
                    "output": result.output,
                    "quality_score": result.quality_score,
                    "cost": 0.0,
                }
            return None

        except Exception as e:
            logger.debug(f"Free API execution failed: {e}")
            return None

    async def _try_paid_execution(self, task: Dict, **kwargs) -> Optional[Dict]:
        """Try execution on paid agents (Claude, GPT, etc)"""
        logger.info("Attempting paid execution (not yet implemented)")
        return None

    def get_cost_summary(self) -> Dict:
        """Get cost summary"""
        return {
            "total_cost": self.cost_so_far,
            "budget_limit": self.budget_limit,
            "budget_remaining": self.budget_limit - self.cost_so_far,
            "executions": len(self.execution_log),
        }
