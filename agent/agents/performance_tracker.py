"""
Agent Performance Tracking

Learn from agent performance and optimize future selection.
"""

from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentPerformanceTracker:
    """Track and learn from agent performance"""

    def __init__(self):
        self.performance_history: List[Dict] = []
        self.agent_ratings: Dict[str, Dict] = {}

    def record_execution(self, agent_name: str, task_type: str, success: bool, duration_ms: int, quality_score: float, cost: float = 0.0):
        """Record agent execution performance"""

        record = {
            "agent_name": agent_name,
            "task_type": task_type,
            "success": success,
            "duration_ms": duration_ms,
            "quality_score": quality_score,
            "cost": cost,
            "timestamp": datetime.now().isoformat(),
        }

        self.performance_history.append(record)
        self._update_agent_rating(agent_name, task_type, success, quality_score)

    def _update_agent_rating(self, agent_name: str, task_type: str, success: bool, quality_score: float):
        """Update agent rating based on performance"""

        if agent_name not in self.agent_ratings:
            self.agent_ratings[agent_name] = {
                "total_executions": 0,
                "successful_executions": 0,
                "average_quality": 0.0,
                "by_task_type": {},
            }

        rating = self.agent_ratings[agent_name]
        rating["total_executions"] += 1

        if success:
            rating["successful_executions"] += 1

        # Update average quality
        old_avg = rating["average_quality"]
        total = rating["total_executions"]
        rating["average_quality"] = (old_avg * (total - 1) + quality_score) / total

        # Track by task type
        if task_type not in rating["by_task_type"]:
            rating["by_task_type"][task_type] = {
                "total": 0,
                "successful": 0,
                "average_quality": 0.0,
            }

        task_rating = rating["by_task_type"][task_type]
        task_rating["total"] += 1
        if success:
            task_rating["successful"] += 1

        old_task_avg = task_rating["average_quality"]
        task_rating["average_quality"] = (old_task_avg * (task_rating["total"] - 1) + quality_score) / task_rating["total"]

    def get_best_agent_for_task(self, task_type: str, budget_limit: float = 0.0) -> str:
        """Recommend best agent for task based on historical performance"""

        best_agent = None
        best_score = -1

        for agent_name, rating in self.agent_ratings.items():
            if task_type not in rating["by_task_type"]:
                continue

            task_rating = rating["by_task_type"][task_type]

            if task_rating["total"] < 2:  # Need at least 2 executions
                continue

            # Score based on quality and success rate
            success_rate = task_rating["successful"] / task_rating["total"]
            quality = task_rating["average_quality"]
            score = (success_rate * 0.6) + (quality * 0.4)

            if score > best_score:
                best_score = score
                best_agent = agent_name

        return best_agent if best_agent else "default"

    def get_agent_statistics(self, agent_name: str) -> Dict:
        """Get detailed statistics for an agent"""

        if agent_name not in self.agent_ratings:
            return {"error": f"No data for agent {agent_name}"}

        rating = self.agent_ratings[agent_name]
        success_rate = (
            rating["successful_executions"] / rating["total_executions"]
            if rating["total_executions"] > 0
            else 0.0
        )

        return {
            "agent_name": agent_name,
            "total_executions": rating["total_executions"],
            "successful_executions": rating["successful_executions"],
            "success_rate": success_rate,
            "average_quality": rating["average_quality"],
            "by_task_type": rating["by_task_type"],
        }

    def get_summary_statistics(self) -> Dict:
        """Get summary statistics for all agents"""

        total_executions = sum(r["total_executions"] for r in self.agent_ratings.values())
        total_successes = sum(r["successful_executions"] for r in self.agent_ratings.values())

        return {
            "total_agents_tracked": len(self.agent_ratings),
            "total_executions": total_executions,
            "total_successes": total_successes,
            "overall_success_rate": total_successes / total_executions if total_executions > 0 else 0.0,
            "average_quality": sum(r["average_quality"] for r in self.agent_ratings.values()) / len(self.agent_ratings) if self.agent_ratings else 0.0,
        }

    def identify_improvement_opportunities(self) -> List[Dict]:
        """Identify where new agents would help"""

        opportunities = []

        # Find task types with low success rates
        task_success_rates: Dict[str, List[float]] = {}

        for record in self.performance_history:
            task_type = record["task_type"]
            if task_type not in task_success_rates:
                task_success_rates[task_type] = []

            task_success_rates[task_type].append(1.0 if record["success"] else 0.0)

        for task_type, rates in task_success_rates.items():
            if len(rates) >= 5:  # Need at least 5 data points
                avg_success = sum(rates) / len(rates)

                if avg_success < 0.70:
                    opportunities.append({
                        "reason": "Low success rate",
                        "task_type": task_type,
                        "success_rate": avg_success,
                        "recommendation": f"Create specialized agent for {task_type}",
                    })

        return opportunities
