"""
Source Discovery Engine

Automatically discovers and bridges to required data sources.
Determines optimal connection strategy for each source.
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SourceDiscoveryEngine:
    """Discovers data sources and creates connectors"""

    def __init__(self):
        self.known_sources = {
            "financial": ["yahoo-finance", "alpha-vantage", "crypto-compare", "polygon.io"],
            "news": ["hackernews", "newsapi", "reddit", "medium"],
            "weather": ["openweathermap", "weatherapi", "wttr.in"],
            "social": ["twitter-api", "reddit-api", "hacker-news-api"],
            "technical": ["github-api", "stack-overflow", "npm-registry"],
            "market": ["yahoo-finance", "coinmarketcap", "alpha-vantage"],
            "trends": ["google-trends", "pytrends"],
        }

        self.source_strategies = {
            # (source_name, strategy)
            "hackernews": "free_api",
            "reddit": "free_api",
            "weather": "free_api",
            "openweathermap": "free_api",
            "github": "free_api",
            "yahoo-finance": "web_scrape",
            "crypto-compare": "free_api",
            "newsapi": "free_api_with_key",
            "twitter": "rss_scrape",
            "coinmarketcap": "web_scrape",
        }

        self.source_connectors: Dict = {}

    def discover_sources(self, requirement: str) -> List[str]:
        """
        Discover relevant data sources for a requirement

        Args:
            requirement: Natural language requirement (e.g., "I need financial data")

        Returns:
            List of relevant source names
        """

        keywords = self._extract_keywords(requirement)
        categories = self._map_to_categories(keywords)

        relevant_sources = []
        for category in categories:
            if category in self.known_sources:
                relevant_sources.extend(self.known_sources[category])

        return self._deduplicate_and_rank(relevant_sources)

    def bridge_to_source(self, source_name: str, free_only: bool = True) -> Optional[Dict]:
        """
        Create or retrieve connector to data source

        Args:
            source_name: Name of the source
            free_only: Only use free options

        Returns:
            Connector configuration dict
        """

        if source_name in self.source_connectors:
            return self.source_connectors[source_name]

        strategy = self._determine_strategy(source_name, free_only)
        connector = self._create_connector(source_name, strategy)

        if connector:
            self.source_connectors[source_name] = connector
            logger.info(f"Created connector for {source_name} using {strategy}")

        return connector

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from requirement"""
        # Simple keyword extraction
        keywords = []
        text_lower = text.lower()

        for category, sources in self.known_sources.items():
            if category in text_lower:
                keywords.append(category)

        for source in self.source_strategies.keys():
            if source.replace("-", " ") in text_lower:
                keywords.append(source)

        return keywords

    def _map_to_categories(self, keywords: List[str]) -> List[str]:
        """Map keywords to source categories"""
        categories = []

        category_keywords = {
            "financial": ["stock", "price", "crypto", "forex", "market"],
            "news": ["news", "article", "blog", "headline"],
            "weather": ["weather", "climate", "temperature"],
            "social": ["twitter", "reddit", "social", "sentiment"],
            "technical": ["github", "code", "repository", "npm"],
            "market": ["market", "stock", "crypto", "commodity"],
            "trends": ["trend", "google trends", "popular"],
        }

        for keyword in keywords:
            for category, matches in category_keywords.items():
                if keyword in matches or any(m in keyword for m in matches):
                    if category not in categories:
                        categories.append(category)

        return categories

    def _deduplicate_and_rank(self, sources: List[str]) -> List[str]:
        """Remove duplicates and rank by reliability"""
        seen = set()
        unique = []

        for source in sources:
            if source not in seen:
                unique.append(source)
                seen.add(source)

        # Rank by strategy (free_api preferred, then others)
        def rank_key(source):
            strategy = self.source_strategies.get(source, "unknown")
            if strategy == "free_api":
                return 0
            elif strategy == "free_api_with_key":
                return 1
            elif strategy == "web_scrape":
                return 2
            elif strategy == "rss_scrape":
                return 3
            else:
                return 4

        unique.sort(key=rank_key)
        return unique

    def _determine_strategy(self, source_name: str, free_only: bool) -> str:
        """Determine connection strategy for source"""
        return self.source_strategies.get(source_name, "web_scrape")

    def _create_connector(self, source_name: str, strategy: str) -> Optional[Dict]:
        """Create connector configuration"""

        if strategy == "free_api":
            return {
                "type": "api",
                "strategy": "free_api",
                "source": source_name,
                "requires_key": False,
                "rate_limit": "varies",
            }

        elif strategy == "free_api_with_key":
            return {
                "type": "api",
                "strategy": "free_api_with_key",
                "source": source_name,
                "requires_key": True,
                "rate_limit": "varies",
            }

        elif strategy == "web_scrape":
            return {
                "type": "web_scraper",
                "strategy": "web_scrape",
                "source": source_name,
                "requires_key": False,
                "libraries": ["beautifulsoup4", "requests"],
            }

        elif strategy == "rss_scrape":
            return {
                "type": "rss_feed",
                "strategy": "rss_scrape",
                "source": source_name,
                "requires_key": False,
                "libraries": ["feedparser"],
            }

        return None

    def get_source_stats(self) -> Dict:
        """Get statistics about known sources"""
        return {
            "total_categories": len(self.known_sources),
            "total_sources": sum(len(v) for v in self.known_sources.values()),
            "categories": list(self.known_sources.keys()),
            "active_connectors": len(self.source_connectors),
        }
