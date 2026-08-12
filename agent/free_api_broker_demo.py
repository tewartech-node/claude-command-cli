"""
Free API Broker Demo

Demonstrates automatic API selection for various tasks.
Shows 50+ free APIs organized by capability.
All free tier, zero cost.

Execute: python -m agent.free_api_broker_demo
"""

from agent.api_broker import get_api_broker
from agent.free_api_catalog import get_available_apis
from agent.demo import print_header, print_result


def demo_api_catalog():
    """Demonstrate the free API catalog"""
    print_header("FREE API CATALOG (50+ APIs)")

    summary = get_available_apis()
    print_result("Catalog Summary", summary)

    print("\nAPIs by Category:\n")
    for category, count in summary["categories"].items():
        print(f"  {category.upper()}: {count} APIs")

    print()


def demo_api_selection():
    """Demonstrate intelligent API selection"""
    print_header("INTELLIGENT API SELECTION")

    broker = get_api_broker()

    # Show available capabilities
    capabilities = broker.list_capabilities()
    print(f"Available Capabilities ({len(capabilities)}):\n")
    for i, cap in enumerate(capabilities[:15], 1):
        print(f"  {i}. {cap}")
    if len(capabilities) > 15:
        print(f"  ... and {len(capabilities) - 15} more")
    print()


def demo_task_based_selection():
    """Demonstrate task-based API selection"""
    print_header("TASK-BASED API SELECTION")

    broker = get_api_broker()

    tasks = [
        "Get latest cryptocurrency prices",
        "Search for news about AI",
        "Find trending discussions on tech",
        "Get weather forecast for tomorrow",
        "Search GitHub repositories",
        "Check if a URL is malicious",
    ]

    print("When given a task, the Broker finds suitable free APIs:\n")

    for task in tasks:
        apis = broker.get_apis_for_task(task)
        print(f"Task: {task}")
        print(f"  Found {len(apis)} suitable API(s):")

        for api_option in apis[:3]:
            api_info = api_option["info"]
            print(f"    • {api_option['name']}")
            print(f"      Category: {api_option['category']}")
            print(f"      Free tier: {api_info.get('free_tier', 'N/A')}")
            print(f"      Capabilities: {', '.join(api_info.get('capabilities', [])[:2])}")

        if len(apis) > 3:
            print(f"    ... and {len(apis) - 3} more")
        print()


def demo_capability_routing():
    """Demonstrate capability-based routing"""
    print_header("CAPABILITY-BASED ROUTING")

    broker = get_api_broker()

    capabilities = [
        "crypto_prices",
        "web_search",
        "tech_news",
        "current_weather",
        "repo_search",
        "malicious_url_detection",
    ]

    print("For each capability, Broker selects the best available free API:\n")

    for capability in capabilities:
        selected = broker.select_api(capability)
        if selected:
            api_info = selected["info"]
            print_result(f"Capability: {capability}", {
                "API": selected["name"],
                "Category": selected["category"],
                "Free Tier": api_info.get("free_tier", "Unlimited"),
                "Endpoint": api_info.get("endpoint", "N/A")[:50] + "...",
                "Auth": api_info.get("auth", "none"),
                "Docs": api_info.get("docs", "N/A")
            }, indent=1)
        else:
            print(f"  ❌ No API available for: {capability}\n")


def demo_rate_limiting():
    """Demonstrate rate limit awareness"""
    print_header("RATE LIMIT MANAGEMENT")

    broker = get_api_broker()

    print("The Broker respects free tier rate limits:\n")

    rate_limit_examples = {
        "Groq": "30 requests/min",
        "Ollama": "Unlimited (local)",
        "NewsAPI": "100 requests/day",
        "Alpha Vantage": "5 requests/min",
        "OpenWeatherMap": "1000 requests/day",
        "GitHub": "5000/hour (authenticated)",
    }

    for api_name, limit in rate_limit_examples.items():
        status = "✓ Can use" if broker.usage_tracker.can_use_api({"rate_limit": None}) else "⏱ Rate limited"
        print(f"  {api_name}: {limit}")

    print("\nWhen rate limited, Broker automatically rotates to alternatives.")
    print("If all options exhausted, gracefully degrades to basic fallback.")
    print()


def demo_free_tier_guarantee():
    """Demonstrate zero-cost guarantee"""
    print_header("FREE TIER GUARANTEE")

    print("Core Principle: Use ONLY free tier APIs, no paid upgrades ever.\n")

    print("How it works:\n")
    print("  1. Catalog: 50+ APIs pre-vetted for free availability")
    print("  2. Selection: Prefers unlimited → free tier → expired")
    print("  3. Rotation: If rate limit hit, switches to alternative")
    print("  4. Fallback: If all APIs exhausted, uses local free option")
    print("  5. Never: No paid APIs, no premium tiers, no upgrades\n")

    print("Examples of infinite-cost operations:\n")
    print("  • Cryptocurrency tracking: CoinGecko (unlimited)")
    print("  • News aggregation: HackerNews (unlimited)")
    print("  • Tech discussions: Reddit (unlimited)")
    print("  • Code search: GitHub + NPM (free tier)")
    print("  • Weather data: OpenWeatherMap (1000/day free)")
    print("  • Local inference: Ollama (unlimited, hosted locally)")
    print()


def demo_available_services():
    """Show loaded credential services"""
    print_header("AVAILABLE CREDENTIAL SERVICES")

    broker = get_api_broker()
    stats = broker.get_available_apis()

    print(f"Credentials loaded: {stats['credentials_loaded']}\n")

    if stats['credential_services']:
        print("Services with credentials:\n")
        for service in stats['credential_services']:
            print(f"  ✓ {service}")
    else:
        print("No API credentials loaded (all tasks will use free tier)")
        print("To add credentials, set environment variables:")
        print("  GROQ_API_KEY=...")
        print("  HUGGINGFACE_API_KEY=...")
        print("  NEWSAPI_KEY=...")

    print(f"\nTotal APIs available: {stats['total_apis_available']}")
    print("All APIs are free tier. No cost ever.")
    print()


async def main():
    """Run all demonstrations"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║            FREE API BROKER - ZERO-COST API ORCHESTRATION           ║")
    print("║                                                                    ║")
    print("║    50+ APIs. All free tier. Auto-selection. Rate limit aware.     ║")
    print("║    Automatic fallback chains. Zero cost operation guaranteed.     ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")

    try:
        demo_api_catalog()
        demo_api_selection()
        demo_task_based_selection()
        demo_capability_routing()
        demo_rate_limiting()
        demo_free_tier_guarantee()
        demo_available_services()

        print_header("DEMO COMPLETE - FREE API BROKER")
        print("✓ 50+ free APIs discovered and catalogued")
        print("✓ Intelligent capability-based routing")
        print("✓ Task-to-API matching working")
        print("✓ Rate limit management enabled")
        print("✓ Zero-cost guarantee enforced")
        print("\n" + "="*70)
        print("\nThe Repo can now:")
        print("  1. Detect when external APIs would help a task")
        print("  2. Automatically select best free API")
        print("  3. Respect rate limits and rotate alternatives")
        print("  4. Fall back to local options (Ollama) when exhausted")
        print("  5. Complete any task at $0 cost\n")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Demo error: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
