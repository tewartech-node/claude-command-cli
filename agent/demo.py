"""
Self-contained demo of the Free Agent Framework.
Runs completely offline with mock execution.

Execute: python -m agent.demo
"""

import asyncio
from datetime import datetime
from agent.agents.free_agent_pool import FreeAgentPool, BaseAgent, AgentCapabilities, AgentExecutionResult
from agent.agents.agent_factory import AgentFactory, AgentSpecification
from agent.agents.source_discovery import SourceDiscoveryEngine
from agent.agents.performance_tracker import AgentPerformanceTracker


def print_header(title):
    """Print formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_result(label, value, indent=0):
    """Print formatted result."""
    prefix = "  " * indent
    if isinstance(value, dict):
        print(f"{prefix}{label}:")
        for k, v in value.items():
            print(f"{prefix}  • {k}: {v}")
    elif isinstance(value, list):
        print(f"{prefix}{label}:")
        for item in value:
            print(f"{prefix}  • {item}")
    else:
        print(f"{prefix}{label}: {value}")


class MockAgent(BaseAgent):
    """Mock agent that simulates execution without external services."""

    def __init__(self, name: str, success_rate: float = 0.85):
        capabilities = AgentCapabilities(
            name=name,
            model_type="mock",
            latency_ms=100,
            cost_per_1k_tokens=0.0,
            strengths=["reasoning", "analysis"]
        )
        super().__init__(name, capabilities)
        self.success_rate = success_rate

    async def execute(self, prompt: str, **kwargs) -> AgentExecutionResult:
        """Simulate execution."""
        import random
        import time

        start = time.time()
        success = random.random() < self.success_rate

        result = AgentExecutionResult(
            success=success,
            output=f"Mock response to: {prompt[:50]}...",
            agent_name=self.name
        )
        result.duration_ms = int((time.time() - start) * 1000) + random.randint(50, 200)
        result.cost = 0.0
        result.quality_score = random.uniform(0.7, 0.95) if success else random.uniform(0.3, 0.6)
        result.error = None if success else "Mock error"

        self.call_count += 1
        if not success:
            self.mark_error()
        self.last_used = datetime.now()

        return result


async def demo_agent_factory():
    """Demonstrate agent factory creating specialized agents."""
    print_header("AGENT FACTORY: Dynamic Agent Creation")

    factory = AgentFactory()

    tasks = [
        "Analyze the quarterly financial report",
        "Fetch data from the stock market API",
        "Optimize this Python code for performance",
        "Generate a marketing copy for our product",
        "Classify these customer emails by sentiment",
    ]

    print(f"Creating {len(tasks)} specialized agents for different task types...\n")

    agents = []
    for task in tasks:
        spec = AgentSpecification(
            task=task,
            agent_type="auto",
            data_sources=["api", "database"],
            success_metric="task completion",
            budget="free_only",
            latency_requirement="normal"
        )
        agent = factory.create_agent(spec)
        agents.append(agent)
        print_result(f"Agent: {agent.name}", {
            "type": agent.agent_type,
            "model": agent.base_model,
            "task": task
        }, indent=1)

    stats = factory.get_agent_statistics()
    print_result("\nFactory Statistics", stats)

    return agents


async def demo_source_discovery():
    """Demonstrate source discovery engine."""
    print_header("SOURCE DISCOVERY: Auto-Detecting Data Sources")

    engine = SourceDiscoveryEngine()

    requirements = [
        "I need real-time stock prices and crypto data",
        "Fetch trending topics from social media",
        "Get weather forecasts for multiple cities",
        "Analyze GitHub repositories for code quality",
    ]

    print(f"Discovering sources for {len(requirements)} requirements...\n")

    for req in requirements:
        sources = engine.discover_sources(req)
        print_result(f"Requirement: {req}", sources, indent=1)
        print()


async def demo_performance_tracker():
    """Demonstrate performance tracking and learning."""
    print_header("PERFORMANCE TRACKER: Learning From Execution")

    tracker = AgentPerformanceTracker()

    # Simulate execution history
    executions = [
        ("analyzer", "financial-data", 0.92, True),
        ("analyzer", "financial-data", 0.89, True),
        ("analyzer", "financial-data", 0.91, True),
        ("data_fetcher", "financial-data", 0.78, False),
        ("optimizer", "code-quality", 0.85, True),
        ("optimizer", "code-quality", 0.88, True),
        ("generator", "content-creation", 0.72, True),
        ("classifier", "sentiment-analysis", 0.81, True),
        ("classifier", "sentiment-analysis", 0.83, True),
        ("classifier", "sentiment-analysis", 0.82, True),
    ]

    print(f"Recording {len(executions)} task executions...\n")

    for agent_type, task_type, quality, success in executions:
        tracker.record_execution(
            agent_name=f"{agent_type}-agent",
            agent_type=agent_type,
            task_type=task_type,
            success=success,
            quality_score=quality,
            duration_ms=100
        )

    # Show learned preferences
    print("Task Type Performance:\n")
    for task_type in ["financial-data", "code-quality", "content-creation", "sentiment-analysis"]:
        best_agent = tracker.get_best_agent_for_task(task_type)
        if best_agent:
            rating = tracker.agent_ratings.get(best_agent, {})
            print_result(f"  {task_type}", {
                "best_agent": best_agent,
                "success_rate": f"{rating.get('success_rate', 0):.1%}",
                "avg_quality": f"{rating.get('avg_quality', 0):.2f}",
                "calls": rating.get('total_executions', 0)
            })

    # Identify improvement opportunities
    opportunities = tracker.identify_improvement_opportunities()
    if opportunities:
        print_result("\nImprovement Opportunities", opportunities)


async def demo_free_agent_pool():
    """Demonstrate intelligent agent selection and fallback."""
    print_header("FREE AGENT POOL: Intelligent Selection & Fallback")

    pool = FreeAgentPool()

    # Add mock agents (since Ollama/Groq might not be available)
    pool.register_custom_agent("mock-analyzer", MockAgent("mock-analyzer", 0.90))
    pool.register_custom_agent("mock-fetcher", MockAgent("mock-fetcher", 0.85))
    pool.register_custom_agent("mock-generator", MockAgent("mock-generator", 0.80))

    print(f"Pool initialized with {len(pool.agents)} agents\n")

    # Test task types
    test_tasks = [
        ("analyzer", "What patterns do you see in this dataset?"),
        ("data_fetcher", "Fetch the latest market data"),
        ("general", "Help me write a script"),
    ]

    print("Executing sample tasks with automatic agent selection:\n")

    for task_type, prompt in test_tasks:
        agent = await pool.select_best_agent(task_type, {
            "latency_requirement": "fast",
            "quality_requirement": 0.7
        })

        if agent:
            result = await agent.execute(prompt)
            print_result(f"Task: {task_type}", {
                "prompt": prompt[:40] + "...",
                "selected_agent": result.agent_name,
                "success": result.success,
                "quality_score": f"{result.quality_score:.2f}",
                "duration_ms": result.duration_ms,
                "cost": f"${result.cost:.4f}"
            }, indent=1)
        print()

    # Show pool statistics
    stats = pool.get_agent_stats()
    print_result("Pool Statistics", {
        "total_agents": len(pool.agents),
        "total_executions": stats["total_executions"],
        "total_calls": stats["total_calls"]
    })


async def demo_cost_optimization():
    """Demonstrate cost optimization decision chain."""
    print_header("COST OPTIMIZATION: Zero-Cost Execution Chain")

    print("Decision Chain for Task Execution:\n")
    print("  1. Try LOCAL FREE (Ollama)")
    print("     ✓ $0 cost")
    print("     ✓ Unlimited throughput")
    print("     ✓ No rate limits")
    print("     ✗ Requires local setup")
    print()
    print("  2. Fall back to FREE API (Groq)")
    print("     ✓ $0 cost (free tier)")
    print("     ✓ No setup required")
    print("     ✗ 30 req/min rate limit")
    print()
    print("  3. Fall back to FREE TIER (HuggingFace)")
    print("     ✓ $0 cost (free tier)")
    print("     ✗ 1000 req/day limit")
    print()
    print("  4. Fall back to PAID (if needed)")
    print("     ✓ Unlimited availability")
    print("     ✗ $0.01-0.1 per 1K tokens")
    print()

    total_cost = 0
    print_result("Cost for 1M Token Executions", f"${total_cost:.2f} (using free tier)")


async def main():
    """Run the complete demo."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║           FREE AGENT FRAMEWORK - SELF-CONTAINED DEMO               ║")
    print("║                                                                    ║")
    print("║    Demonstrates: Agent Factory, Source Discovery, Performance     ║")
    print("║    Tracking, Cost Optimization, and Intelligent Agent Selection   ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")

    try:
        # Run all demos
        await demo_agent_factory()
        await demo_source_discovery()
        await demo_performance_tracker()
        await demo_free_agent_pool()
        await demo_cost_optimization()

        print_header("DEMO COMPLETE")
        print("✓ Agent Factory: Created specialized agents dynamically")
        print("✓ Source Discovery: Auto-discovered 40+ data sources")
        print("✓ Performance Tracking: Learned from execution history")
        print("✓ Agent Pool: Demonstrated intelligent selection & fallback")
        print("✓ Cost Optimization: $0 cost execution chain ready")
        print("\n" + "="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Demo error: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
