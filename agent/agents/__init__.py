"""
Free Agent Sourcing Framework

Enables The Brain to:
1. Utilize free/open-source AI agents (Ollama, Groq, HuggingFace)
2. Create specialized agents dynamically for specific tasks
3. Automatically detect requirements and spawn agents
4. Optimize cost by prioritizing free options
5. Learn and improve agent selection over time
6. Access 50+ free APIs for any external capability needed
"""

from .free_agent_pool import FreeAgentPool
from .agent_factory import AgentFactory
from .source_discovery import SourceDiscoveryEngine
from .cost_optimizer import CostOptimizedExecutor
from .performance_tracker import AgentPerformanceTracker
from .brain_integration import BrainRequirementDetector
from .api_broker import ApiBroker, get_api_broker, select_api, get_apis_for_task
from .free_api_catalog import FREE_API_CATALOG, get_available_apis, get_apis_by_capability
from .credential_manager import CredentialManager, get_credential, has_credential, get_available_services

__all__ = [
    "FreeAgentPool",
    "AgentFactory",
    "SourceDiscoveryEngine",
    "CostOptimizedExecutor",
    "AgentPerformanceTracker",
    "BrainRequirementDetector",
    "ApiBroker",
    "get_api_broker",
    "select_api",
    "get_apis_for_task",
    "FREE_API_CATALOG",
    "get_available_apis",
    "get_apis_by_capability",
    "CredentialManager",
    "get_credential",
    "has_credential",
    "get_available_services",
]
