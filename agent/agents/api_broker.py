"""
Free API Broker

Central hub for API selection, routing, and capability matching.
Automatically selects best free API for each task.
Respects rate limits and rotates between options.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .free_api_catalog import (
    FREE_API_CATALOG,
    get_apis_by_capability,
    get_api,
    get_available_apis,
)
from .credential_manager import (
    get_credential,
    has_credential,
    get_available_services,
)

logger = logging.getLogger(__name__)


class APIUsageTracker:
    """Tracks API usage against rate limits"""

    def __init__(self):
        self.usage: Dict[str, List[datetime]] = {}

    def record_usage(self, api_name: str):
        """Record an API call"""
        if api_name not in self.usage:
            self.usage[api_name] = []
        self.usage[api_name].append(datetime.now())

    def can_use_api(self, api_info: dict) -> bool:
        """Check if API can be used based on rate limits"""
        api_name = api_info.get("name", "unknown")

        if api_info.get("rate_limit") is None:
            # Unlimited API
            return True

        if api_name not in self.usage:
            return True

        rate_limit = api_info["rate_limit"]
        rate_window = api_info["rate_window"]

        # Get recent calls within the window
        cutoff = datetime.now() - timedelta(seconds=rate_window)
        recent_calls = [t for t in self.usage[api_name] if t > cutoff]

        return len(recent_calls) < rate_limit

    def get_usage_summary(self) -> dict:
        """Get usage summary"""
        return {
            api_name: len(calls)
            for api_name, calls in self.usage.items()
        }


class ApiBroker:
    """Routes requests to appropriate free APIs"""

    def __init__(self):
        self.usage_tracker = APIUsageTracker()
        self.credentials = get_available_services()
        logger.info(f"API Broker initialized with {len(self.credentials)} credential(s)")

    def select_api(self, capability: str, preferred_category: Optional[str] = None) -> Optional[Dict]:
        """
        Select best available API for a capability

        Args:
            capability: Required capability (e.g., "crypto_prices", "web_search")
            preferred_category: Preferred API category

        Returns:
            API info dict or None if no suitable API found
        """
        # Find APIs that support this capability
        matching_apis = get_apis_by_capability(capability)

        if not matching_apis:
            logger.warning(f"No APIs found for capability: {capability}")
            return None

        # Filter by availability and rate limits
        available_apis = []
        for api_option in matching_apis:
            api_info = api_option["info"]

            # Check if rate limit allows
            if not self.usage_tracker.can_use_api(api_info):
                logger.debug(f"API {api_option['name']} rate limited")
                continue

            # Check if requires credential
            if api_info.get("auth") != "none" and api_info.get("env_var"):
                if not has_credential(api_option["name"]):
                    logger.debug(f"API {api_option['name']} no credential available")
                    continue

            available_apis.append(api_option)

        if not available_apis:
            logger.warning(f"No available APIs for capability: {capability}")
            return None

        # Prefer free tier unlimited or preferred category
        if preferred_category:
            preferred = [a for a in available_apis if a["category"] == preferred_category]
            if preferred:
                selected = preferred[0]
            else:
                selected = available_apis[0]
        else:
            # Prefer unlimited APIs first
            unlimited = [a for a in available_apis if a["info"].get("rate_limit") is None]
            if unlimited:
                selected = unlimited[0]
            else:
                selected = available_apis[0]

        logger.info(f"Selected {selected['name']} for capability: {capability}")
        return selected

    def get_api_for_task(self, task_description: str) -> List[Dict]:
        """
        Get recommended APIs for a task description

        Args:
            task_description: Natural language task description

        Returns:
            List of suitable APIs
        """
        # Map keywords to capabilities
        keyword_capability_map = {
            "news": "trending",
            "crypto": "crypto_prices",
            "stock": "stock_data",
            "weather": "current_weather",
            "search": "web_search",
            "code": ["repo_search", "commits"],
            "github": "repo_search",
            "npm": "package_search",
            "security": "malicious_url_detection",
            "image": "image_search",
        }

        relevant_apis = []
        task_lower = task_description.lower()

        for keyword, capabilities in keyword_capability_map.items():
            if keyword in task_lower:
                cap_list = capabilities if isinstance(capabilities, list) else [capabilities]
                for cap in cap_list:
                    apis = get_apis_by_capability(cap)
                    relevant_apis.extend(apis)

        # Deduplicate
        seen = set()
        unique_apis = []
        for api in relevant_apis:
            api_id = api["name"]
            if api_id not in seen:
                unique_apis.append(api)
                seen.add(api_id)

        return unique_apis

    def get_available_apis(self) -> dict:
        """Get summary of available APIs"""
        summary = get_available_apis()
        summary["credentials_loaded"] = len(self.credentials)
        summary["credential_services"] = self.credentials
        return summary

    def get_api_details(self, category: str, api_name: str) -> Optional[Dict]:
        """Get detailed info about a specific API"""
        return get_api(category, api_name)

    def get_usage_stats(self) -> dict:
        """Get API usage statistics"""
        return {
            "usage_summary": self.usage_tracker.get_usage_summary(),
            "credentials_available": len(self.credentials),
            "total_apis_available": sum(
                len(apis) for apis in FREE_API_CATALOG.values()
            ),
        }

    def list_capabilities(self) -> List[str]:
        """List all available capabilities across all APIs"""
        capabilities = set()
        for category in FREE_API_CATALOG.values():
            for api_info in category.values():
                capabilities.update(api_info.get("capabilities", []))
        return sorted(list(capabilities))


# Global broker instance
_api_broker = ApiBroker()


def get_api_broker() -> ApiBroker:
    """Get global API broker instance"""
    return _api_broker


def select_api(capability: str, preferred_category: Optional[str] = None) -> Optional[Dict]:
    """Select API for capability (convenience function)"""
    return _api_broker.select_api(capability, preferred_category)


def get_apis_for_task(task_description: str) -> List[Dict]:
    """Get APIs for task (convenience function)"""
    return _api_broker.get_api_for_task(task_description)
