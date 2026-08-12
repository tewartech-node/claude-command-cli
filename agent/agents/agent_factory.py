"""
Agent Factory

Dynamically creates specialized agents for specific tasks.
Generates prompts, binds tools, and manages agent lifecycle.
"""

import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentSpecification:
    """Specification for creating an agent"""
    task: str
    agent_type: str  # "analyzer", "data_fetcher", "optimizer", etc.
    data_sources: List[str]
    success_metric: str
    budget: str  # "free_only", "free_preferred", "any"
    latency_requirement: str  # "realtime", "fast", "normal", "hourly"
    tools_required: List[str] = None
    max_retries: int = 3


class SpecializedAgent:
    """A dynamically created specialized agent"""

    def __init__(
        self,
        name: str,
        agent_type: str,
        system_prompt: str,
        base_model: str,
        tools: List[Callable],
        success_metric: str,
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.agent_type = agent_type
        self.system_prompt = system_prompt
        self.base_model = base_model
        self.tools = {tool.__name__: tool for tool in tools}
        self.success_metric = success_metric
        self.created_at = datetime.now()
        self.execution_count = 0
        self.success_count = 0
        self.last_error = None

    async def execute(self, context: Dict = None, **kwargs) -> Dict:
        """Execute the agent"""
        self.execution_count += 1

        try:
            # Import here to use whatever agent pool is available
            from .free_agent_pool import FreeAgentPool

            pool = FreeAgentPool()

            # Build execution prompt
            execution_prompt = self._build_execution_prompt(context, kwargs)

            # Execute with agent pool
            result = await pool.execute_with_fallback(
                execution_prompt,
                task_type=self.agent_type,
                latency_requirement="normal"
            )

            if result.success:
                self.success_count += 1
                return {
                    "success": True,
                    "output": result.output,
                    "agent_id": self.id,
                    "agent_name": self.name,
                    "execution_time_ms": result.duration_ms,
                    "cost": result.cost,
                }
            else:
                self.last_error = result.error
                return {
                    "success": False,
                    "error": result.error,
                    "agent_id": self.id,
                    "agent_name": self.name,
                }

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            self.last_error = str(e)
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.id,
                "agent_name": self.name,
            }

    def _build_execution_prompt(self, context: Dict, kwargs: Dict) -> str:
        """Build the actual execution prompt"""

        prompt = self.system_prompt

        if context:
            prompt += f"\n\nCurrent Context:\n{self._format_context(context)}"

        if kwargs:
            prompt += f"\n\nExecution Parameters:\n{self._format_kwargs(kwargs)}"

        return prompt

    def _format_context(self, context: Dict) -> str:
        """Format context for prompt"""
        lines = []
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def _format_kwargs(self, kwargs: Dict) -> str:
        """Format kwargs for prompt"""
        lines = []
        for key, value in kwargs.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def get_success_rate(self) -> float:
        """Get agent success rate"""
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count


class AgentFactory:
    """Creates specialized agents on demand"""

    def __init__(self):
        self.agent_registry: Dict[str, SpecializedAgent] = {}
        self.agent_specs: Dict[str, AgentSpecification] = {}
        self.task_history: List[Dict] = []

    def create_agent(self, spec: AgentSpecification) -> SpecializedAgent:
        """Create a specialized agent from specification"""

        logger.info(f"Creating agent for task: {spec.task}")

        # Classify task type
        agent_type = self._classify_task(spec.task)

        # Select base model based on budget and latency
        base_model = self._select_base_model(agent_type, spec)

        # Determine tools needed
        tools = self._determine_tools(agent_type, spec)

        # Generate system prompt
        system_prompt = self._generate_system_prompt(agent_type, spec, tools)

        # Create agent instance
        agent = SpecializedAgent(
            name=f"{agent_type}_{uuid.uuid4().hex[:8]}",
            agent_type=agent_type,
            system_prompt=system_prompt,
            base_model=base_model,
            tools=tools,
            success_metric=spec.success_metric,
        )

        # Register
        self.agent_registry[agent.id] = agent
        self.agent_specs[agent.id] = spec

        logger.info(f"Agent created: {agent.name} (id: {agent.id})")

        return agent

    def _classify_task(self, task: str) -> str:
        """Classify task type"""

        task_lower = task.lower()

        if any(w in task_lower for w in ["analyze", "examine", "inspect", "assess"]):
            return "analyzer"
        elif any(w in task_lower for w in ["fetch", "get", "retrieve", "scrape", "crawl"]):
            return "data_fetcher"
        elif any(w in task_lower for w in ["optimize", "improve", "enhance", "refactor"]):
            return "optimizer"
        elif any(w in task_lower for w in ["generate", "create", "synthesize", "produce"]):
            return "generator"
        elif any(w in task_lower for w in ["classify", "categorize", "label", "identify"]):
            return "classifier"
        elif any(w in task_lower for w in ["summarize", "extract", "aggregate", "digest"]):
            return "summarizer"
        elif any(w in task_lower for w in ["predict", "forecast", "estimate", "project"]):
            return "predictor"
        else:
            return "general"

    def _select_base_model(self, agent_type: str, spec: AgentSpecification) -> str:
        """Select best free model for task"""

        # Model capabilities (free only)
        models = {
            "analyzer": {
                "free_local": "mistral:latest",
                "free_api": "groq-llama2",
                "score": 10,
            },
            "data_fetcher": {
                "free_local": "llama2:13b",
                "free_api": "huggingface",
                "score": 8,
            },
            "optimizer": {
                "free_local": "mistral:latest",
                "free_api": "groq-llama2",
                "score": 9,
            },
            "generator": {
                "free_local": "llama2:13b",
                "free_api": "huggingface",
                "score": 7,
            },
            "classifier": {
                "free_local": "mistral:latest",
                "free_api": "huggingface",
                "score": 8,
            },
            "summarizer": {
                "free_local": "llama2:13b",
                "free_api": "huggingface",
                "score": 8,
            },
            "predictor": {
                "free_local": "mistral:latest",
                "free_api": "groq-llama2",
                "score": 9,
            },
            "general": {
                "free_local": "mistral:latest",
                "free_api": "groq-llama2",
                "score": 7,
            },
        }

        model_spec = models.get(agent_type, models["general"])

        # Prefer local for latency-sensitive tasks
        if spec.latency_requirement == "realtime":
            return model_spec["free_local"]

        # Default to local for cost savings
        return model_spec["free_local"]

    def _determine_tools(self, agent_type: str, spec: AgentSpecification) -> List[Callable]:
        """Determine which tools agent needs"""

        tools = []

        # Data access tools
        if agent_type in ["data_fetcher", "analyzer"]:
            tools.extend([
                self._tool_web_fetch,
                self._tool_json_parse,
            ])

        # Analysis tools
        if agent_type in ["analyzer", "predictor"]:
            tools.extend([
                self._tool_statistics,
                self._tool_correlation,
            ])

        # Generation tools
        if agent_type in ["generator", "summarizer"]:
            tools.extend([
                self._tool_format_output,
            ])

        # Optimization tools
        if agent_type == "optimizer":
            tools.extend([
                self._tool_performance_profile,
                self._tool_suggest_improvements,
            ])

        # Always add storage and logging
        tools.extend([
            self._tool_store_result,
            self._tool_log_execution,
        ])

        return tools

    def _generate_system_prompt(self, agent_type: str, spec: AgentSpecification, tools: List) -> str:
        """Generate specialized system prompt"""

        tools_str = "\n".join([f"- {t.__name__}()" for t in tools])

        prompt = f"""You are a specialized {agent_type} agent.

OBJECTIVE: {spec.task}

SUCCESS CRITERIA: {spec.success_metric}

DATA SOURCES: {', '.join(spec.data_sources)}

LATENCY REQUIREMENT: {spec.latency_requirement}

BUDGET CONSTRAINT: {spec.budget}

AVAILABLE TOOLS:
{tools_str}

INSTRUCTIONS:
1. Break down the task into logical steps
2. Use appropriate tools for each step
3. Validate data quality and assumptions
4. Report results with confidence scores
5. Handle errors gracefully and report limitations

EXECUTION RULES:
- Always prioritize quality over speed
- Validate assumptions before proceeding
- Log all decisions and reasoning
- Stop if success metric cannot be met
- Report any unexpected findings

Begin execution:"""

        return prompt

    def get_agent(self, agent_id: str) -> Optional[SpecializedAgent]:
        """Retrieve agent by ID"""
        return self.agent_registry.get(agent_id)

    def list_agents(self, agent_type: Optional[str] = None) -> List[SpecializedAgent]:
        """List agents, optionally filtered by type"""

        agents = list(self.agent_registry.values())

        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]

        return agents

    def get_agent_statistics(self) -> Dict:
        """Get statistics about created agents"""

        total_agents = len(self.agent_registry)
        total_executions = sum(a.execution_count for a in self.agent_registry.values())
        total_successes = sum(a.success_count for a in self.agent_registry.values())

        success_rate = (
            total_successes / total_executions if total_executions > 0 else 0
        )

        agents_by_type = {}
        for agent in self.agent_registry.values():
            atype = agent.agent_type
            if atype not in agents_by_type:
                agents_by_type[atype] = []
            agents_by_type[atype].append(agent)

        return {
            "total_agents_created": total_agents,
            "total_executions": total_executions,
            "total_successes": total_successes,
            "overall_success_rate": success_rate,
            "agents_by_type": {k: len(v) for k, v in agents_by_type.items()},
        }

    # Tool implementations
    def _tool_web_fetch(self, url: str) -> Dict:
        """Fetch content from URL"""
        try:
            import requests
            response = requests.get(url, timeout=10)
            return {"success": True, "content": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _tool_json_parse(self, data: str) -> Dict:
        """Parse JSON data"""
        try:
            import json
            return {"success": True, "data": json.loads(data)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _tool_statistics(self, data: List[float]) -> Dict:
        """Calculate statistics"""
        try:
            import statistics
            return {
                "success": True,
                "mean": statistics.mean(data),
                "median": statistics.median(data),
                "stdev": statistics.stdev(data) if len(data) > 1 else 0,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _tool_correlation(self, data1: List[float], data2: List[float]) -> Dict:
        """Calculate correlation between datasets"""
        try:
            import statistics
            if len(data1) != len(data2) or len(data1) < 2:
                return {"success": False, "error": "Invalid data"}

            mean1 = statistics.mean(data1)
            mean2 = statistics.mean(data2)

            numerator = sum((data1[i] - mean1) * (data2[i] - mean2) for i in range(len(data1)))
            denominator = (
                (sum((x - mean1) ** 2 for x in data1) * sum((x - mean2) ** 2 for x in data2)) ** 0.5
            )

            correlation = numerator / denominator if denominator != 0 else 0

            return {"success": True, "correlation": correlation}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _tool_format_output(self, data: Any, format_type: str = "json") -> Dict:
        """Format output"""
        try:
            import json
            if format_type == "json":
                return {"success": True, "output": json.dumps(data, indent=2)}
            return {"success": True, "output": str(data)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _tool_performance_profile(self, code: str) -> Dict:
        """Profile code performance"""
        return {"success": True, "analysis": "Performance analysis would run here"}

    def _tool_suggest_improvements(self, analysis: str) -> Dict:
        """Suggest improvements"""
        return {"success": True, "suggestions": "Improvement suggestions would be generated here"}

    def _tool_store_result(self, key: str, value: Any) -> Dict:
        """Store result for later access"""
        return {"success": True, "stored_key": key}

    def _tool_log_execution(self, message: str) -> Dict:
        """Log execution message"""
        logger.info(f"Agent execution: {message}")
        return {"success": True, "logged": True}
