"""
Free Agent Pool Manager

Manages pool of free local and API-based agents.
Prioritizes zero-cost options, falls back to paid only when necessary.
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentCapabilities:
    """Agent capability specification"""
    name: str
    model_type: str  # "ollama", "groq", "huggingface", "openrouter"
    max_tokens: int = 4096
    latency_ms: int = 100
    cost_per_1k_tokens: float = 0.0
    strengths: List[str] = field(default_factory=list)
    throughput: str = "1 req/s"
    rate_limit: Optional[str] = None
    availability: str = "always"  # "always", "daytime", "offpeak"


class AgentExecutionResult:
    """Result from agent execution"""

    def __init__(self, success: bool, output: Any, agent_name: str):
        self.success = success
        self.output = output
        self.agent_name = agent_name
        self.timestamp = datetime.now()
        self.duration_ms = 0
        self.cost = 0.0
        self.quality_score = 0.0  # 0-1 scale
        self.error = None


class BaseAgent:
    """Base class for all agent types"""

    def __init__(self, name: str, capabilities: AgentCapabilities):
        self.name = name
        self.capabilities = capabilities
        self.is_available = True
        self.last_used = None
        self.call_count = 0
        self.error_count = 0

    async def execute(self, prompt: str, **kwargs) -> AgentExecutionResult:
        """Execute agent with given prompt"""
        raise NotImplementedError

    def mark_error(self):
        """Mark that agent encountered an error"""
        self.error_count += 1
        self.is_available = self.error_count < 5

    def get_health_score(self) -> float:
        """Calculate agent health (0-1)"""
        if self.call_count == 0:
            return 1.0
        error_rate = self.error_count / self.call_count
        return max(0.0, 1.0 - error_rate)


class OllamaAgent(BaseAgent):
    """Local Ollama agent"""

    def __init__(self, model: str = "mistral:latest", base_url: str = "http://localhost:11434"):
        capabilities = AgentCapabilities(
            name=f"ollama-{model.split(':')[0]}",
            model_type="ollama",
            latency_ms=50,
            cost_per_1k_tokens=0.0,
            strengths=["reasoning", "code", "analysis", "general"],
            throughput="5 req/s local",
        )
        super().__init__(capabilities.name, capabilities)
        self.model = model
        self.base_url = base_url
        self.client = None  # Lazy-load ollama client

    async def execute(self, prompt: str, **kwargs) -> AgentExecutionResult:
        """Execute using local Ollama"""
        try:
            import requests

            start_time = datetime.now()

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=kwargs.get("timeout", 30)
            )

            if response.status_code == 200:
                data = response.json()
                result = AgentExecutionResult(
                    success=True,
                    output=data.get("response", ""),
                    agent_name=self.name
                )
                result.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                result.cost = 0.0
                result.quality_score = 0.85  # Local is generally good quality
                self.call_count += 1
                self.last_used = datetime.now()
                return result
            else:
                raise Exception(f"Ollama error: {response.status_code}")

        except Exception as e:
            logger.error(f"Ollama execution failed: {e}")
            self.mark_error()
            result = AgentExecutionResult(False, None, self.name)
            result.error = str(e)
            return result


class GroqAgent(BaseAgent):
    """Groq free API agent"""

    def __init__(self, model: str = "llama2-70b-4096", api_key: Optional[str] = None):
        capabilities = AgentCapabilities(
            name=f"groq-{model}",
            model_type="groq",
            latency_ms=200,
            cost_per_1k_tokens=0.0,
            strengths=["reasoning", "complex-tasks", "long-context"],
            throughput="30 req/min free",
            rate_limit="30 req/min free tier",
            availability="always"
        )
        super().__init__(capabilities.name, capabilities)
        self.model = model
        self.api_key = api_key
        self.client = None  # Lazy-load groq client

    async def execute(self, prompt: str, **kwargs) -> AgentExecutionResult:
        """Execute using Groq free tier"""
        try:
            try:
                from groq import Groq
            except ImportError:
                raise ImportError("Install groq: pip install groq")

            if not self.client:
                self.client = Groq(api_key=self.api_key)

            start_time = datetime.now()

            message = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 1024),
                temperature=kwargs.get("temperature", 0.7),
            )

            result = AgentExecutionResult(
                success=True,
                output=message.choices[0].message.content,
                agent_name=self.name
            )
            result.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            result.cost = 0.0  # Free tier
            result.quality_score = 0.88
            self.call_count += 1
            self.last_used = datetime.now()
            return result

        except Exception as e:
            logger.error(f"Groq execution failed: {e}")
            self.mark_error()
            result = AgentExecutionResult(False, None, self.name)
            result.error = str(e)
            return result


class HuggingFaceAgent(BaseAgent):
    """HuggingFace Inference API agent"""

    def __init__(self, model: str = "gpt2", api_key: Optional[str] = None):
        capabilities = AgentCapabilities(
            name=f"huggingface-{model}",
            model_type="huggingface",
            latency_ms=500,
            cost_per_1k_tokens=0.0,
            strengths=["text-generation", "summarization", "classification"],
            throughput="1000 req/day free",
            availability="always"
        )
        super().__init__(capabilities.name, capabilities)
        self.model = model
        self.api_key = api_key

    async def execute(self, prompt: str, **kwargs) -> AgentExecutionResult:
        """Execute using HuggingFace free tier"""
        try:
            try:
                from huggingface_hub import InferenceClient
            except ImportError:
                raise ImportError("Install huggingface-hub: pip install huggingface-hub")

            client = InferenceClient(api_key=self.api_key)
            start_time = datetime.now()

            output = client.text_generation(
                prompt,
                max_new_tokens=kwargs.get("max_tokens", 512),
                temperature=kwargs.get("temperature", 0.7),
            )

            result = AgentExecutionResult(
                success=True,
                output=output,
                agent_name=self.name
            )
            result.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            result.cost = 0.0  # Free tier
            result.quality_score = 0.75
            self.call_count += 1
            self.last_used = datetime.now()
            return result

        except Exception as e:
            logger.error(f"HuggingFace execution failed: {e}")
            self.mark_error()
            result = AgentExecutionResult(False, None, self.name)
            result.error = str(e)
            return result


class FreeAgentPool:
    """Manages pool of free agents with intelligent selection and fallback"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.execution_history: List[Dict] = []
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize default free agents"""

        # Local Ollama agents (zero cost, requires local deployment)
        try:
            self.agents["mistral-7b"] = OllamaAgent("mistral:latest")
            self.agents["llama2-13b"] = OllamaAgent("llama2:13b")
            logger.info("Ollama agents initialized (requires local Ollama running)")
        except Exception as e:
            logger.warning(f"Ollama initialization failed: {e}")

        # Free API agents
        try:
            self.agents["groq-llama2"] = GroqAgent("llama2-70b-4096")
            logger.info("Groq agent initialized")
        except Exception as e:
            logger.warning(f"Groq initialization failed: {e}")

        try:
            self.agents["huggingface"] = HuggingFaceAgent("gpt2")
            logger.info("HuggingFace agent initialized")
        except Exception as e:
            logger.warning(f"HuggingFace initialization failed: {e}")

    async def select_best_agent(self, task_type: str, requirements: Dict) -> Optional[BaseAgent]:
        """Select best agent for task based on type and requirements"""

        candidate_agents = []

        for agent in self.agents.values():
            if not agent.is_available:
                continue

            score = self._score_agent(agent, task_type, requirements)
            if score > 0:
                candidate_agents.append((agent, score))

        if not candidate_agents:
            logger.warning(f"No available agents for task: {task_type}")
            return None

        # Sort by score (highest first)
        candidate_agents.sort(key=lambda x: x[1], reverse=True)
        return candidate_agents[0][0]

    def _score_agent(self, agent: BaseAgent, task_type: str, requirements: Dict) -> float:
        """Score agent for task (0-100)"""

        score = 50  # Base score

        # Strength matching
        if task_type in agent.capabilities.strengths:
            score += 30

        # Health score
        score += agent.get_health_score() * 20

        # Latency preference
        if requirements.get("latency_requirement") == "realtime" and agent.capabilities.latency_ms < 500:
            score += 10
        elif requirements.get("latency_requirement") == "fast" and agent.capabilities.latency_ms < 200:
            score += 5

        # Cost (free is always preferred)
        if agent.capabilities.cost_per_1k_tokens == 0:
            score += 20

        return score

    async def execute_with_fallback(self, prompt: str, task_type: str = "general", **kwargs) -> AgentExecutionResult:
        """Execute task with automatic fallback"""

        requirements = {
            "latency_requirement": kwargs.get("latency_requirement", "normal"),
            "quality_requirement": kwargs.get("quality_requirement", 0.7),
        }

        # Try to find best agent
        agent = await self.select_best_agent(task_type, requirements)

        if not agent:
            logger.error("No agents available")
            result = AgentExecutionResult(False, None, "none")
            result.error = "No available agents"
            return result

        # Execute with selected agent
        result = await agent.execute(prompt, **kwargs)

        # If failed and score below threshold, try next best agent
        if not result.success or result.quality_score < requirements.get("quality_requirement", 0.7):
            logger.info(f"Agent {agent.name} failed, trying fallback")
            # Try alternative agents
            for alt_agent in self.agents.values():
                if alt_agent.name != agent.name and alt_agent.is_available:
                    result = await alt_agent.execute(prompt, **kwargs)
                    if result.success:
                        break

        self.execution_history.append({
            "task_type": task_type,
            "agent": result.agent_name,
            "success": result.success,
            "timestamp": datetime.now(),
            "duration_ms": result.duration_ms,
            "cost": result.cost,
        })

        return result

    async def execute_parallel(self, tasks: List[Dict]) -> List[AgentExecutionResult]:
        """Execute multiple tasks concurrently"""

        coroutines = [
            self.execute_with_fallback(
                task["prompt"],
                task_type=task.get("type", "general"),
                **task.get("kwargs", {})
            )
            for task in tasks
        ]

        results = await asyncio.gather(*coroutines, return_exceptions=True)

        return [r if isinstance(r, AgentExecutionResult) else AgentExecutionResult(False, None, "error") for r in results]

    def get_agent_stats(self) -> Dict:
        """Get statistics for all agents"""

        stats = {}
        total_calls = sum(a.call_count for a in self.agents.values())

        for agent in self.agents.values():
            stats[agent.name] = {
                "calls": agent.call_count,
                "errors": agent.error_count,
                "health": agent.get_health_score(),
                "availability": agent.is_available,
                "cost_per_1k": agent.capabilities.cost_per_1k_tokens,
                "latency_ms": agent.capabilities.latency_ms,
            }

        return {
            "agents": stats,
            "total_executions": len(self.execution_history),
            "total_calls": total_calls,
        }

    def register_custom_agent(self, name: str, agent: BaseAgent):
        """Register a custom agent"""
        self.agents[name] = agent
        logger.info(f"Registered custom agent: {name}")
