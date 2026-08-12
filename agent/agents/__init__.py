"""
Free Agent Sourcing Framework

Enables The Brain to:
1. Utilize free/open-source AI agents (Ollama, Groq, HuggingFace)
2. Create specialized agents dynamically for specific tasks
3. Automatically detect requirements and spawn agents
4. Optimize cost by prioritizing free options
5. Learn and improve agent selection over time
"""

from .free_agent_pool import FreeAgentPool
from .agent_factory import AgentFactory
from .source_discovery import SourceDiscoveryEngine
from .cost_optimizer import CostOptimizedExecutor
from .performance_tracker import AgentPerformanceTracker
from .brain_integration import BrainRequirementDetector

__all__ = [
    "FreeAgentPool",
    "AgentFactory",
    "SourceDiscoveryEngine",
    "CostOptimizedExecutor",
    "AgentPerformanceTracker",
    "BrainRequirementDetector",
]
