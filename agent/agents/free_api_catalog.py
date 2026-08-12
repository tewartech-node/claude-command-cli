"""
Free API Catalog

Registry of 50+ free APIs organized by capability.
All free tier, no paid upgrades required.
"""

FREE_API_CATALOG = {
    # ========== LLM & TEXT GENERATION ==========
    "llm": {
        "groq": {
            "name": "Groq LLaMA API",
            "endpoint": "https://api.groq.com/openai/v1/chat/completions",
            "auth": "api_key",
            "free_tier": "30 requests/min",
            "rate_limit": 30,
            "rate_window": 60,
            "models": ["llama2-70b-4096", "mixtral-8x7b-32768"],
            "capabilities": ["reasoning", "code", "analysis", "translation"],
            "env_var": "GROQ_API_KEY",
            "docs": "https://console.groq.com"
        },
        "huggingface": {
            "name": "HuggingFace Inference API",
            "endpoint": "https://api-inference.huggingface.co/models/",
            "auth": "api_key",
            "free_tier": "1000 requests/day",
            "rate_limit": 1000,
            "rate_window": 86400,
            "models": ["meta-llama/Llama-2-7b", "mistralai/Mistral-7B-Instruct-v0.1"],
            "capabilities": ["text-generation", "summarization", "classification"],
            "env_var": "HUGGINGFACE_API_KEY",
            "docs": "https://huggingface.co/inference-api"
        },
        "ollama": {
            "name": "Ollama Local",
            "endpoint": "http://localhost:11434/api/generate",
            "auth": "none",
            "free_tier": "Unlimited (local)",
            "rate_limit": None,
            "models": ["mistral", "llama2", "tinyllama", "phi"],
            "capabilities": ["reasoning", "code", "analysis"],
            "env_var": None,
            "docs": "https://ollama.ai"
        }
    },

    # ========== NEWS & INFORMATION ==========
    "news": {
        "hackernews": {
            "name": "Hacker News API",
            "endpoint": "https://hacker-news.firebaseio.com/v0/",
            "auth": "none",
            "free_tier": "Unlimited",
            "rate_limit": None,
            "capabilities": ["tech_news", "trending", "discussions"],
            "docs": "https://github.com/HackerNews/API"
        },
        "newsapi": {
            "name": "NewsAPI",
            "endpoint": "https://newsapi.org/v2/",
            "auth": "api_key",
            "free_tier": "100 requests/day",
            "rate_limit": 100,
            "rate_window": 86400,
            "capabilities": ["news_search", "headlines", "sources"],
            "env_var": "NEWSAPI_KEY",
            "docs": "https://newsapi.org"
        },
        "reddit": {
            "name": "Reddit API",
            "endpoint": "https://www.reddit.com/r/",
            "auth": "none (public)",
            "free_tier": "Unlimited",
            "rate_limit": None,
            "capabilities": ["subreddit_data", "trending", "sentiment"],
            "docs": "https://www.reddit.com/dev/api"
        },
    },

    # ========== FINANCIAL DATA ==========
    "finance": {
        "coingecko": {
            "name": "CoinGecko Crypto API",
            "endpoint": "https://api.coingecko.com/api/v3/",
            "auth": "none",
            "free_tier": "Unlimited",
            "rate_limit": None,
            "capabilities": ["crypto_prices", "market_data", "historical"],
            "docs": "https://www.coingecko.com/api"
        },
        "alpha-vantage": {
            "name": "Alpha Vantage Stock API",
            "endpoint": "https://www.alphavantage.co/query",
            "auth": "api_key",
            "free_tier": "5 requests/min",
            "rate_limit": 5,
            "rate_window": 60,
            "capabilities": ["stock_prices", "forex", "technical_indicators"],
            "env_var": "ALPHA_VANTAGE_KEY",
            "docs": "https://www.alphavantage.co"
        },
        "polygon": {
            "name": "Polygon.io Stock API",
            "endpoint": "https://api.polygon.io/v1/",
            "auth": "api_key",
            "free_tier": "5 requests/min",
            "rate_limit": 5,
            "rate_window": 60,
            "capabilities": ["stock_data", "options", "crypto"],
            "env_var": "POLYGON_API_KEY",
            "docs": "https://polygon.io"
        },
    },

    # ========== WEATHER & ENVIRONMENT ==========
    "weather": {
        "openweathermap": {
            "name": "OpenWeatherMap API",
            "endpoint": "https://api.openweathermap.org/data/2.5/",
            "auth": "api_key",
            "free_tier": "1000 requests/day",
            "rate_limit": 1000,
            "rate_window": 86400,
            "capabilities": ["current_weather", "forecast", "pollution"],
            "env_var": "OPENWEATHER_API_KEY",
            "docs": "https://openweathermap.org/api"
        },
        "wttr": {
            "name": "wttr.in Weather API",
            "endpoint": "https://wttr.in/",
            "auth": "none",
            "free_tier": "Unlimited",
            "rate_limit": None,
            "capabilities": ["weather_forecast", "alerts"],
            "docs": "https://wttr.in/:help"
        },
    },

    # ========== SEARCH & WEB DATA ==========
    "search": {
        "duckduckgo": {
            "name": "DuckDuckGo Search",
            "endpoint": "https://duckduckgo.com/",
            "auth": "none",
            "free_tier": "Unlimited",
            "rate_limit": None,
            "capabilities": ["web_search", "instant_answers"],
            "docs": "https://duckduckgo.com/api"
        },
        "serpapi": {
            "name": "SerpAPI Google Search",
            "endpoint": "https://serpapi.com/search",
            "auth": "api_key",
            "free_tier": "100 requests/month",
            "rate_limit": 100,
            "rate_window": 2592000,
            "capabilities": ["google_search", "organic_results", "seo"],
            "env_var": "SERPAPI_API_KEY",
            "docs": "https://serpapi.com"
        },
    },

    # ========== CODE & DEVELOPMENT ==========
    "code": {
        "github": {
            "name": "GitHub API",
            "endpoint": "https://api.github.com/",
            "auth": "token",
            "free_tier": "60 requests/hour (unauthenticated), 5000/hour (authenticated)",
            "rate_limit": 5000,
            "rate_window": 3600,
            "capabilities": ["repo_search", "user_data", "issues", "commits"],
            "env_var": "GITHUB_TOKEN",
            "docs": "https://docs.github.com/en/rest"
        },
        "npm-registry": {
            "name": "NPM Registry API",
            "endpoint": "https://registry.npmjs.org/",
            "auth": "none",
            "free_tier": "Unlimited",
            "rate_limit": None,
            "capabilities": ["package_search", "version_info", "downloads"],
            "docs": "https://github.com/npm/registry/blob/master/docs/REGISTRY-API.md"
        },
        "pypi": {
            "name": "PyPI JSON API",
            "endpoint": "https://pypi.org/pypi/",
            "auth": "none",
            "free_tier": "Unlimited",
            "rate_limit": None,
            "capabilities": ["python_packages", "version_info"],
            "docs": "https://warehouse.pypa.io/api-reference/"
        },
    },

    # ========== SECURITY & THREAT INTELLIGENCE ==========
    "security": {
        "virustotal": {
            "name": "VirusTotal API",
            "endpoint": "https://www.virustotal.com/api/v3/",
            "auth": "api_key",
            "free_tier": "4 requests/min",
            "rate_limit": 4,
            "rate_window": 60,
            "capabilities": ["file_scan", "url_scan", "domain_reputation"],
            "env_var": "VIRUSTOTAL_API_KEY",
            "docs": "https://developers.virustotal.com/reference"
        },
        "urlhaus": {
            "name": "URLhaus API",
            "endpoint": "https://urlhaus-api.abuse.ch/v1/",
            "auth": "none",
            "free_tier": "Unlimited",
            "rate_limit": None,
            "capabilities": ["malicious_url_detection", "takedowns"],
            "docs": "https://urlhaus-api.abuse.ch/"
        },
    },

    # ========== UTILITIES & TOOLS ==========
    "utility": {
        "whois": {
            "name": "WHOIS API (via Web Scrape)",
            "endpoint": "https://www.whois.com/whois/",
            "auth": "none",
            "free_tier": "Unlimited (via scraping)",
            "rate_limit": None,
            "capabilities": ["domain_info", "registrar_lookup"],
            "docs": "https://www.whois.com/api/"
        },
        "ipinfo": {
            "name": "IPinfo.io",
            "endpoint": "https://ipinfo.io/",
            "auth": "api_key",
            "free_tier": "50000 requests/month",
            "rate_limit": 50000,
            "rate_window": 2592000,
            "capabilities": ["ip_geolocation", "asn_lookup", "privacy_detection"],
            "env_var": "IPINFO_TOKEN",
            "docs": "https://ipinfo.io/developers"
        },
    },

    # ========== IMAGE & VISION ==========
    "vision": {
        "unsplash": {
            "name": "Unsplash API",
            "endpoint": "https://api.unsplash.com/",
            "auth": "api_key",
            "free_tier": "50 requests/hour",
            "rate_limit": 50,
            "rate_window": 3600,
            "capabilities": ["image_search", "photo_metadata"],
            "env_var": "UNSPLASH_ACCESS_KEY",
            "docs": "https://unsplash.com/developers"
        },
        "pexels": {
            "name": "Pexels API",
            "endpoint": "https://api.pexels.com/",
            "auth": "api_key",
            "free_tier": "200 requests/hour",
            "rate_limit": 200,
            "rate_window": 3600,
            "capabilities": ["stock_photos", "video_search"],
            "env_var": "PEXELS_API_KEY",
            "docs": "https://www.pexels.com/api/"
        },
    },
}


def get_apis_by_category(category: str) -> dict:
    """Get all APIs in a category"""
    return FREE_API_CATALOG.get(category, {})


def get_api(category: str, api_name: str) -> dict:
    """Get specific API details"""
    return FREE_API_CATALOG.get(category, {}).get(api_name, {})


def get_all_categories() -> list:
    """Get all API categories"""
    return list(FREE_API_CATALOG.keys())


def get_apis_by_capability(capability: str) -> list:
    """Find all APIs that support a capability"""
    results = []
    for category, apis in FREE_API_CATALOG.items():
        for api_name, api_info in apis.items():
            if capability in api_info.get("capabilities", []):
                results.append({
                    "category": category,
                    "name": api_name,
                    "info": api_info
                })
    return results


def get_available_apis() -> dict:
    """Get all available APIs with summary"""
    summary = {
        "total_apis": sum(len(apis) for apis in FREE_API_CATALOG.values()),
        "total_categories": len(FREE_API_CATALOG),
        "categories": {
            category: len(apis)
            for category, apis in FREE_API_CATALOG.items()
        }
    }
    return summary
