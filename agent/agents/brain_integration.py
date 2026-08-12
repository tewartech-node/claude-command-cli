"""
Brain Integration

Automatic detection of Brain requirements and agent spawning.
"""

from typing import Dict, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class BrainRequirementDetector:
    """Detects when Brain needs agent assistance and spawns appropriate agents"""

    def __init__(self, brain_state_provider=None):
        """
        Initialize detector

        Args:
            brain_state_provider: Callable that returns current brain state dict
        """
        self.brain_state_provider = brain_state_provider
        self.pending_agents = []
        self.completed_agents = []

    async def monitor_and_respond(self, check_interval: int = 60):
        """
        Continuously monitor Brain state and spawn agents as needed

        Args:
            check_interval: Seconds between state checks
        """
        logger.info("Starting Brain monitoring")

        while True:
            try:
                state = self._get_brain_state()

                # Check various requirement triggers
                requirements = self._detect_requirements(state)

                for requirement in requirements:
                    await self._spawn_agent_for_requirement(requirement)

                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(check_interval)

    def _get_brain_state(self) -> Dict:
        """Get current Brain state"""
        if self.brain_state_provider:
            return self.brain_state_provider()

        # Default mock state
        return {
            "decision_success_rate": 0.75,
            "database_size_mb": 400,
            "telemetry_gap_hours": 2,
            "code_issues_critical": 0,
            "pattern_extraction_rate": 1.0 / 86400,
            "average_confidence": 0.65,
            "cpu_usage_percent": 45,
            "memory_usage_mb": 250,
        }

    def _detect_requirements(self, state: Dict) -> list:
        """Detect requirements based on state"""
        requirements = []

        # Check success rate
        if state.get("decision_success_rate", 1.0) < 0.70:
            requirements.append({
                "type": "improve_decision_quality",
                "reason": f"Low success rate: {state['decision_success_rate']}",
                "budget": 0,
            })

        # Check database size
        if state.get("database_size_mb", 0) > 500:
            requirements.append({
                "type": "optimize_storage",
                "reason": f"Database too large: {state['database_size_mb']}MB",
                "budget": 0,
            })

        # Check telemetry freshness
        if state.get("telemetry_gap_hours", 0) > 6:
            requirements.append({
                "type": "fetch_missing_telemetry",
                "reason": f"Telemetry gap: {state['telemetry_gap_hours']} hours",
                "budget": 0,
            })

        # Check code quality
        if state.get("code_issues_critical", 0) > 0:
            requirements.append({
                "type": "analyze_code_issues",
                "reason": f"Critical code issues: {state['code_issues_critical']}",
                "budget": 0,
            })

        # Check pattern extraction
        if state.get("pattern_extraction_rate", 0) < 1.0 / 86400:
            requirements.append({
                "type": "extract_behavioral_patterns",
                "reason": "Low pattern extraction rate",
                "budget": 0,
            })

        return requirements

    async def _spawn_agent_for_requirement(self, requirement: Dict):
        """Spawn an agent to handle requirement"""
        from .agent_factory import AgentFactory, AgentSpecification

        logger.info(f"Spawning agent for: {requirement['type']}")

        factory = AgentFactory()

        # Create appropriate agent specification
        spec = self._create_specification(requirement)

        # Create agent
        agent = factory.create_agent(spec)

        # Execute agent
        try:
            context = self._get_brain_state()
            result = await agent.execute(context=context)

            if result.get("success"):
                logger.info(f"Agent {agent.name} succeeded: {result}")
                self.completed_agents.append(agent)
            else:
                logger.warning(f"Agent {agent.name} failed: {result.get('error')}")

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")

    def _create_specification(self, requirement: Dict) -> 'AgentSpecification':
        """Create agent specification from requirement"""
        from .agent_factory import AgentSpecification

        specs = {
            "improve_decision_quality": AgentSpecification(
                task="Analyze recent decisions and identify patterns causing low success rate",
                agent_type="analyzer",
                data_sources=["decisions", "metrics"],
                success_metric="Identify root causes of low success",
                budget="free_only",
                latency_requirement="hourly",
            ),
            "optimize_storage": AgentSpecification(
                task="Analyze database and recommend storage optimizations",
                agent_type="optimizer",
                data_sources=["database", "storage_metrics"],
                success_metric="Find optimizations yielding >20% reduction",
                budget="free_only",
                latency_requirement="hourly",
            ),
            "fetch_missing_telemetry": AgentSpecification(
                task="Fetch missing telemetry data from configured sources",
                agent_type="data_fetcher",
                data_sources=["telemetry_sources"],
                success_metric="Fill telemetry gaps from recent hours",
                budget="free_only",
                latency_requirement="hourly",
            ),
            "analyze_code_issues": AgentSpecification(
                task="Analyze codebase and identify critical issues",
                agent_type="analyzer",
                data_sources=["codebase"],
                success_metric="Find and categorize all critical issues",
                budget="free_only",
                latency_requirement="hourly",
            ),
            "extract_behavioral_patterns": AgentSpecification(
                task="Extract behavioral patterns from decision history",
                agent_type="analyzer",
                data_sources=["decisions", "outcomes"],
                success_metric="Extract at least 3 new behavioral patterns",
                budget="free_only",
                latency_requirement="daily",
            ),
        }

        requirement_type = requirement.get("type", "generic")
        return specs.get(requirement_type, AgentSpecification(
            task=requirement.get("reason", "Handle requirement"),
            agent_type="general",
            data_sources=[],
            success_metric="Complete assigned task",
            budget="free_only",
            latency_requirement="hourly",
        ))

    def get_status(self) -> Dict:
        """Get detector status"""
        return {
            "pending_agents": len(self.pending_agents),
            "completed_agents": len(self.completed_agents),
            "last_check": None,
        }
