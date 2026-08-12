# Telemetry Ingestion System
## Connecting The Brain to Internet Data Streams

Transform your learning system from isolated to context-aware by ingesting real-time telemetry from internet sources, APIs, and live data streams.

---

## Vision

Currently, The Brain learns from:
- Your email (what you receive)
- Your web traffic (where you go)
- Your decisions (what you choose)

**With telemetry ingestion, it learns from:**
- Global trends (what's happening now)
- Market movements (financial context)
- Weather & events (environmental factors)
- News & social (societal context)
- API data (rich structured data)
- IoT sensors (physical context)
- Real-time streams (instant updates)

**Result:** Smarter decisions based on global context, trend correlation, and event causality.

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│              Internet Data Sources (Real-time)             │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  APIs               Webhooks           Streams             │
│  ├─ News APIs      ├─ GitHub webhooks  ├─ Kafka topics   │
│  ├─ Weather API    ├─ Slack events     ├─ WebSockets     │
│  ├─ Stock APIs     ├─ Custom webhooks  ├─ MQTT feeds     │
│  ├─ Crypto APIs    └─ Webhooks         └─ Server-sent    │
│  ├─ Twitter API    │  │                   events          │
│  ├─ Reddit API     │  └─ 100+ calls/day                   │
│  ├─ Weather.com    │                                      │
│  ├─ OpenWeather    │                                      │
│  ├─ Google Trends  │                                      │
│  ├─ Wikipedia      │                                      │
│  ├─ HackerNews     │                                      │
│  ├─ Sports APIs    │                                      │
│  └─ More...        │                                      │
│                    ↓                                       │
│         ┌──────────────────────────┐                      │
│         │  Telemetry Ingestion     │                      │
│         │  Gateway                 │                      │
│         │  (Rate limiting,         │                      │
│         │   deduplication,         │                      │
│         │   error handling)        │                      │
│         └──────────┬───────────────┘                      │
│                    ↓                                       │
│         ┌──────────────────────────┐                      │
│         │  Data Normalization      │                      │
│         │  & Enrichment            │                      │
│         │  (Transform to Brain     │                      │
│         │   format)                │                      │
│         └──────────┬───────────────┘                      │
│                    ↓                                       │
│         ┌──────────────────────────┐                      │
│         │  Real-time Processing    │                      │
│         │  ├─ Aggregation          │                      │
│         │  ├─ Correlation          │                      │
│         │  ├─ Anomaly detection    │                      │
│         │  └─ Context enrichment   │                      │
│         └──────────┬───────────────┘                      │
│                    ↓                                       │
│         ┌──────────────────────────┐                      │
│         │  Brain Core              │                      │
│         │  ├─ Context awareness    │                      │
│         │  ├─ Trend correlation    │                      │
│         │  ├─ Predictive modeling  │                      │
│         │  └─ Enhanced decisions   │                      │
│         └──────────────────────────┘                      │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Data Sources Available

### 1. News & Content
- **NewsAPI** (newsapi.org) - 38,000+ sources
- **HackerNews API** - Tech trends
- **Reddit API** - Community discussions
- **Guardian API** - Quality journalism
- **NY Times API** - Major news
- **MediaStack** - Global news

### 2. Trends & Social
- **Twitter/X API** - Real-time tweets, trends
- **TikTok Trends** (via unofficial APIs)
- **Google Trends** - Search patterns
- **Wikipedia Trending** - Hot topics
- **YouTube Trends** - Video trends
- **Spotify Charts** - Music trends

### 3. Financial Data
- **Alpha Vantage** - Stock prices, FX
- **Finnhub** - Real-time market data
- **CoinGecko** - Cryptocurrency prices
- **CoinMarketCap** - Crypto rankings
- **Twelve Data** - Financial charts
- **Polygon.io** - Stock/options data

### 4. Weather & Environment
- **OpenWeatherMap** - Current + forecast
- **Weather.gov** - US weather
- **NOAA** - Natural disasters
- **Air Quality API** - Pollution levels
- **GeoDB** - Location data

### 5. System & Development
- **GitHub API** - Repo activity, releases
- **NPM Registry** - Package trends
- **PyPI** - Python package updates
- **Docker Hub** - Container updates
- **CI/CD APIs** - Build status

### 6. IoT & Sensors
- **MQTT Brokers** - Sensor data
- **InfluxDB** - Time-series data
- **Adafruit IO** - IoT platform
- **ThingSpeak** - Sensor streams
- **Custom Webhooks** - Any source

### 7. Real-time Communication
- **WebSocket Streams** - Live updates
- **Server-Sent Events** - Push data
- **Kafka Topics** - Message streams
- **AMQP Queues** - Message brokers
- **gRPC Streams** - Low-latency APIs

---

## Implementation Roadmap

### Phase 1: Core Ingestion (Week 1-2)
```
✅ Telemetry base classes
✅ API client framework
✅ Webhook receiver
✅ Data normalization
✅ Storage in database
✅ 3 free APIs (HackerNews, Weather, RSS)
```

### Phase 2: Popular Sources (Week 3-4)
```
📅 Add 10 major APIs
📅 Rate limiting & retry logic
📅 Credential management
📅 Source health monitoring
📅 Error recovery
```

### Phase 3: Real-time Streams (Week 5-6)
```
📅 WebSocket support
📅 Server-Sent Events
📅 Kafka integration
📅 Stream aggregation
```

### Phase 4: Intelligence Layer (Week 7-8)
```
📅 Correlation engine
📅 Anomaly detection
📅 Context enrichment
📅 Predictive signals
```

---

## Phase 1: Core Implementation

### 1.1 Base Telemetry Classes

```python
# agent/telemetry/base.py

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3

class TelemetrySource(ABC):
    """Base class for all telemetry sources"""
    
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category  # news, trends, financial, weather, etc
        self.last_update = None
        self.data_points = 0
        
    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch data from source"""
        pass
    
    @abstractmethod
    def normalize(self, raw_data: Any) -> Dict[str, Any]:
        """Normalize to Brain format"""
        pass
    
    def store(self, data: Dict[str, Any], db_path: str):
        """Store telemetry in database"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO telemetry
            (source, category, data_json, timestamp, relevance)
            VALUES (?, ?, ?, ?, ?)
        """, (
            self.name,
            self.category,
            json.dumps(data),
            datetime.now().isoformat(),
            data.get('relevance_score', 0.5)
        ))
        
        conn.commit()
        conn.close()
        self.data_points += 1
        self.last_update = datetime.now()
```

### 1.2 Telemetry Gateway

```python
# agent/telemetry/gateway.py

from typing import List, Dict, Any
import asyncio
import aiohttp
from datetime import datetime, timedelta

class TelemetryGateway:
    """Central gateway for ingesting telemetry from multiple sources"""
    
    def __init__(self, db_path: str = "./agent/storage/memory.db"):
        self.db_path = db_path
        self.sources = {}
        self.rate_limiters = {}
        self.cache = {}
        self._init_telemetry_table()
    
    def register_source(self, source: TelemetrySource):
        """Register a telemetry source"""
        self.sources[source.name] = source
        self.rate_limiters[source.name] = RateLimiter(calls_per_hour=100)
    
    async def fetch_all_async(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch from all sources in parallel"""
        tasks = []
        for name, source in self.sources.items():
            if self.rate_limiters[name].allow_request():
                tasks.append(self._fetch_source(source))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def _fetch_source(self, source: TelemetrySource):
        """Fetch from single source with error handling"""
        try:
            data = source.fetch()
            normalized = [source.normalize(item) for item in data]
            
            for item in normalized:
                source.store(item, self.db_path)
            
            return {source.name: normalized}
        except Exception as e:
            self._log_error(source.name, str(e))
            return {source.name: []}
    
    def get_recent_telemetry(self, hours: int = 24) -> Dict[str, Any]:
        """Get recent telemetry by category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = datetime.now() - timedelta(hours=hours)
        cursor.execute("""
            SELECT category, COUNT(*) as count, AVG(relevance) as avg_relevance
            FROM telemetry
            WHERE timestamp > ?
            GROUP BY category
        """, (cutoff.isoformat(),))
        
        results = {}
        for category, count, relevance in cursor.fetchall():
            results[category] = {
                'count': count,
                'avg_relevance': relevance
            }
        
        conn.close()
        return results
```

### 1.3 Free Sources (No Auth Required)

```python
# agent/telemetry/sources/free_sources.py

class HackerNewsSource(TelemetrySource):
    """HackerNews top stories"""
    
    def __init__(self):
        super().__init__("HackerNews", "tech_news")
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Get top 30 stories"""
        import requests
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        story_ids = requests.get(url).json()[:30]
        
        stories = []
        for story_id in story_ids:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            story = requests.get(story_url).json()
            stories.append(story)
        
        return stories
    
    def normalize(self, raw_data: Dict) -> Dict[str, Any]:
        """Normalize HN data"""
        return {
            'source': 'HackerNews',
            'title': raw_data.get('title'),
            'url': raw_data.get('url'),
            'score': raw_data.get('score', 0),
            'comments': raw_data.get('descendants', 0),
            'timestamp': datetime.fromtimestamp(raw_data['time']).isoformat(),
            'category': 'tech_news',
            'relevance_score': min(1.0, raw_data.get('score', 0) / 1000),
        }


class RSSFeedSource(TelemetrySource):
    """Generic RSS feed source"""
    
    def __init__(self, name: str, feed_url: str, category: str):
        super().__init__(name, category)
        self.feed_url = feed_url
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch RSS feed"""
        import feedparser
        feed = feedparser.parse(self.feed_url)
        return feed.entries[:20]
    
    def normalize(self, entry) -> Dict[str, Any]:
        """Normalize RSS entry"""
        return {
            'source': self.name,
            'title': entry.get('title'),
            'link': entry.get('link'),
            'summary': entry.get('summary'),
            'published': entry.get('published'),
            'category': self.category,
            'relevance_score': 0.6,
        }


class WeatherSource(TelemetrySource):
    """OpenWeatherMap free tier"""
    
    def __init__(self, api_key: str, city: str = "auto"):
        super().__init__("Weather", "environment")
        self.api_key = api_key
        self.city = city
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Get current weather"""
        import requests
        url = f"https://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={self.api_key}"
        response = requests.get(url)
        return [response.json()]
    
    def normalize(self, raw_data: Dict) -> Dict[str, Any]:
        """Normalize weather data"""
        weather = raw_data['weather'][0]
        return {
            'source': 'Weather',
            'city': raw_data['name'],
            'temperature': raw_data['main']['temp'],
            'condition': weather['main'],
            'description': weather['description'],
            'humidity': raw_data['main']['humidity'],
            'wind_speed': raw_data['wind'].get('speed', 0),
            'timestamp': datetime.fromtimestamp(raw_data['dt']).isoformat(),
            'category': 'environment',
            'relevance_score': 0.7,
        }


class GoogleTrendsSource(TelemetrySource):
    """Google Search Trends"""
    
    def __init__(self):
        super().__init__("GoogleTrends", "search_trends")
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Get trending searches"""
        # Using unofficial API (pytrends)
        from pytrends.request import TrendReq
        
        pytrends = TrendReq()
        trending = pytrends.trending_searches(pn='united_states')
        
        return [{'keyword': k, 'rank': i} for i, k in enumerate(trending.values)]
    
    def normalize(self, raw_data: Dict) -> Dict[str, Any]:
        """Normalize trend data"""
        return {
            'source': 'GoogleTrends',
            'keyword': raw_data['keyword'],
            'rank': raw_data['rank'],
            'category': 'search_trends',
            'relevance_score': 1.0 - (raw_data['rank'] / 25),  # Higher for top trends
            'timestamp': datetime.now().isoformat(),
        }
```

### 1.4 Database Schema

```python
# Add to diagnostic_engine._init_diagnostics_table()

def _init_telemetry_tables(self):
    """Initialize telemetry storage"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    # Main telemetry table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY,
            source TEXT,
            category TEXT,
            data_json TEXT,
            timestamp TEXT,
            relevance REAL,
            processed INTEGER DEFAULT 0,
            correlated_to TEXT
        )
    """)
    
    # Telemetry aggregates
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry_aggregates (
            id INTEGER PRIMARY KEY,
            category TEXT,
            time_bucket TEXT,
            aggregate_type TEXT,
            value REAL,
            timestamp TEXT
        )
    """)
    
    # Telemetry correlations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry_correlations (
            id INTEGER PRIMARY KEY,
            source1_id INTEGER,
            source2_id INTEGER,
            correlation_strength REAL,
            correlation_type TEXT,
            timestamp TEXT
        )
    """)
    
    conn.commit()
    conn.close()
```

---

## Phase 2: API Integration

### 2.1 Supported APIs (Free Tier)

```python
# agent/telemetry/sources/api_sources.py

class NewsAPISource(TelemetrySource):
    """NewsAPI - Top news from 38,000+ sources"""
    
    def __init__(self, api_key: str):
        super().__init__("NewsAPI", "general_news")
        self.api_key = api_key
    
    def fetch(self) -> List[Dict]:
        import requests
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            'apiKey': self.api_key,
            'language': 'en',
            'sortBy': 'popularity'
        }
        response = requests.get(url, params=params)
        return response.json()['articles'][:20]


class FinancialDataSource(TelemetrySource):
    """Alpha Vantage - Stock market data"""
    
    def __init__(self, api_key: str, symbol: str = "AAPL"):
        super().__init__(f"Stock-{symbol}", "financial")
        self.api_key = api_key
        self.symbol = symbol
    
    def fetch(self) -> List[Dict]:
        import requests
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': self.symbol,
            'apikey': self.api_key
        }
        response = requests.get(url, params=params)
        return [response.json()['Global Quote']]


class CryptoSource(TelemetrySource):
    """CoinGecko - Cryptocurrency prices"""
    
    def __init__(self):
        super().__init__("Crypto", "financial")
    
    def fetch(self) -> List[Dict]:
        import requests
        url = "https://api.coingecko.com/api/v3/global"
        response = requests.get(url)
        data = response.json()
        
        return [{
            'btc': data['data']['btc_market_cap'],
            'eth': data['data']['eth_market_cap'],
            'market_cap': data['data']['total_market_cap'],
            'volume': data['data']['total_volume'],
            'btc_dominance': data['data']['btc_market_cap_percentage']
        }]


class RedditSource(TelemetrySource):
    """Reddit - Community discussions"""
    
    def __init__(self, subreddits: List[str] = None):
        super().__init__("Reddit", "social")
        self.subreddits = subreddits or ['technology', 'worldnews', 'programming']
    
    def fetch(self) -> List[Dict]:
        import praw
        reddit = praw.Reddit(client_id='...', client_secret='...', user_agent='...')
        
        posts = []
        for subreddit in self.subreddits:
            for post in reddit.subreddit(subreddit).hot(limit=10):
                posts.append({
                    'title': post.title,
                    'score': post.score,
                    'subreddit': subreddit,
                    'url': post.url,
                    'comments': post.num_comments
                })
        
        return posts
```

---

## Phase 3: Real-time Streams

### 3.1 WebSocket Support

```python
# agent/telemetry/sources/streams.py

import asyncio
import websockets
import json

class WebSocketSource(TelemetrySource):
    """Generic WebSocket stream receiver"""
    
    def __init__(self, name: str, ws_url: str, category: str):
        super().__init__(name, category)
        self.ws_url = ws_url
        self.buffer = []
    
    async def connect_and_stream(self):
        """Connect to WebSocket and process stream"""
        async with websockets.connect(self.ws_url) as websocket:
            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=30
                    )
                    data = json.loads(message)
                    normalized = self.normalize(data)
                    self.buffer.append(normalized)
                    
                    # Process every 100 items
                    if len(self.buffer) >= 100:
                        self.flush()
                
                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    print(f"WebSocket error: {e}")
                    await asyncio.sleep(5)  # Reconnect
    
    def flush(self):
        """Store buffered data"""
        for item in self.buffer:
            self.store(item, self.db_path)
        self.buffer = []


class KafkaSource(TelemetrySource):
    """Kafka stream consumer"""
    
    def __init__(self, name: str, bootstrap_servers: List[str], topic: str, category: str):
        super().__init__(name, category)
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
    
    async def consume_stream(self):
        """Consume from Kafka topic"""
        from aiokafka import AIOKafkaConsumer
        
        consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=f'brain-{self.name}'
        )
        
        await consumer.start()
        try:
            async for msg in consumer:
                data = json.loads(msg.value.decode())
                normalized = self.normalize(data)
                self.store(normalized, self.db_path)
        finally:
            await consumer.stop()


class MQTTSource(TelemetrySource):
    """MQTT sensor data receiver"""
    
    def __init__(self, name: str, broker: str, topics: List[str], category: str):
        super().__init__(name, category)
        self.broker = broker
        self.topics = topics
    
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        import paho.mqtt.client as mqtt
        
        client = mqtt.Client()
        client.on_message = self._on_message
        client.connect(self.broker, 1883, 60)
        
        for topic in self.topics:
            client.subscribe(topic)
        
        client.loop_start()
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT message"""
        try:
            data = json.loads(msg.payload)
            normalized = self.normalize(data)
            self.store(normalized, self.db_path)
        except:
            pass
```

---

## Phase 4: Intelligence Layer

### 4.1 Correlation Engine

```python
# agent/telemetry/correlation.py

class CorrelationEngine:
    """Find meaningful correlations between telemetry streams"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def find_correlations(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Find strong correlations between events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Get recent telemetry by source
        cursor.execute("""
            SELECT source, AVG(relevance) as avg_rel, COUNT(*) as count
            FROM telemetry
            WHERE timestamp > ?
            GROUP BY source
        """, (cutoff.isoformat(),))
        
        sources_data = cursor.fetchall()
        correlations = []
        
        # Simple correlation: high relevance in multiple sources
        for i, source1 in enumerate(sources_data):
            for source2 in sources_data[i+1:]:
                # Check if both sources had high activity same time
                correlation = self._calculate_correlation(source1, source2)
                if correlation > 0.7:
                    correlations.append({
                        'source1': source1[0],
                        'source2': source2[0],
                        'strength': correlation,
                        'description': f"{source1[0]} correlated with {source2[0]}"
                    })
        
        conn.close()
        return correlations
    
    def detect_anomalies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Detect unusual telemetry patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Compare recent to historical average
        cursor.execute("""
            SELECT category, AVG(relevance) as recent_avg
            FROM telemetry
            WHERE timestamp > datetime('now', ? || ' hours')
            GROUP BY category
        """, (f"-{hours}",))
        
        anomalies = []
        for category, recent in cursor.fetchall():
            # Get historical average
            cursor.execute("""
                SELECT AVG(relevance)
                FROM telemetry
                WHERE category = ?
                AND timestamp < datetime('now', '-7 days')
            """, (category,))
            
            historical = cursor.fetchone()[0] or 0.5
            
            if recent > historical * 1.5:
                anomalies.append({
                    'category': category,
                    'current': recent,
                    'historical': historical,
                    'deviation': recent / historical,
                    'type': 'spike'
                })
        
        conn.close()
        return anomalies
```

### 4.2 Context Enrichment

```python
# agent/telemetry/context.py

class ContextEnricher:
    """Add context to decisions based on telemetry"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_context_for_decision(self, decision_time: datetime) -> Dict[str, Any]:
        """Get relevant context for a decision"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get telemetry from around decision time (+/- 30 min)
        time_window = timedelta(minutes=30)
        start = (decision_time - time_window).isoformat()
        end = (decision_time + time_window).isoformat()
        
        cursor.execute("""
            SELECT source, category, data_json
            FROM telemetry
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY relevance DESC
            LIMIT 20
        """, (start, end))
        
        context = {}
        for source, category, data_json in cursor.fetchall():
            if category not in context:
                context[category] = []
            context[category].append({
                'source': source,
                'data': json.loads(data_json)
            })
        
        conn.close()
        
        return {
            'decision_time': decision_time.isoformat(),
            'context_window': f"±30 minutes",
            'active_telemetry': context,
            'trend_indicators': self._get_trend_indicators(context),
            'anomalies': self._get_active_anomalies(context),
        }
    
    def _get_trend_indicators(self, context: Dict) -> Dict[str, Any]:
        """Extract trend indicators from context"""
        trends = {}
        
        if 'search_trends' in context:
            trends['search_trends'] = [
                t['data'].get('keyword') for t in context['search_trends'][:5]
            ]
        
        if 'financial' in context:
            financial = context['financial'][0]['data']
            trends['market_moving'] = financial.get('score', 0) > 0.7
        
        return trends
    
    def _get_active_anomalies(self, context: Dict) -> List[str]:
        """Get active anomalies from context"""
        anomalies = []
        
        for category, data_list in context.items():
            for item in data_list:
                if item['data'].get('relevance_score', 0) > 0.8:
                    anomalies.append(f"High {category}: {item['source']}")
        
        return anomalies
```

---

## Setup Instructions

### Quick Start: Free Sources Only

```bash
pip install requests feedparser python-dateutil
```

```python
# agent/telemetry/setup.py

from telemetry.gateway import TelemetryGateway
from telemetry.sources.free_sources import (
    HackerNewsSource, RSSFeedSource, WeatherSource, GoogleTrendsSource
)

# Initialize gateway
gateway = TelemetryGateway()

# Register free sources
gateway.register_source(HackerNewsSource())
gateway.register_source(GoogleTrendsSource())
gateway.register_source(WeatherSource())

# Add RSS feeds
gateway.register_source(RSSFeedSource(
    "TechNews",
    "https://feeds.bloomberg.com/markets/news.rss",
    "business_news"
))

# Start collecting (non-blocking)
import asyncio
asyncio.create_task(gateway.fetch_all_async())
```

### With API Keys

```bash
# Add to .env
NEWSAPI_KEY=your_key
ALPHAVANTAGE_KEY=your_key
OPENWEATHERMAP_KEY=your_key
REDDIT_ID=your_id
REDDIT_SECRET=your_secret
```

```python
import os
from telemetry.sources.api_sources import NewsAPISource, FinancialDataSource

gateway.register_source(NewsAPISource(os.getenv('NEWSAPI_KEY')))
gateway.register_source(FinancialDataSource(os.getenv('ALPHAVANTAGE_KEY'), 'AAPL'))
```

---

## Data Flow Example

```
1. HackerNews publishes story: "AI Breakthrough"
   ↓
2. Telemetry Gateway fetches every hour
   ↓
3. Data normalized:
   {
     "source": "HackerNews",
     "title": "AI Breakthrough",
     "score": 500,
     "relevance_score": 0.75,
     "timestamp": "2026-08-12T14:30:00Z"
   }
   ↓
4. Stored in telemetry table
   ↓
5. Brain makes decision related to AI
   ↓
6. Context Enricher adds telemetry context:
   "Decision made while AI news trending"
   ↓
7. Decision confidence increases with context
   ↓
8. Learning correlates: High AI news → Higher engagement
```

---

## Integration with Existing Brain

```python
# In agent/core/agent.py

from telemetry.context import ContextEnricher

class Brain:
    def __init__(self):
        self.enricher = ContextEnricher()
    
    def make_decision(self, scenario):
        # Get regular analysis
        analysis = self.analyze(scenario)
        
        # Add telemetry context
        context = self.enricher.get_context_for_decision(datetime.now())
        
        # Combine: (base_confidence + context_boost)
        context_boost = len(context['active_telemetry']) * 0.05
        final_confidence = min(1.0, analysis['confidence'] + context_boost)
        
        # Store enriched decision
        decision = {
            **analysis,
            'confidence': final_confidence,
            'context': context,
            'telemetry_influenced': len(context['active_telemetry']) > 0
        }
        
        return decision
```

---

## Monitoring Telemetry Health

```python
# agent/telemetry/monitoring.py

class TelemetryMonitor:
    def get_health_status(self) -> Dict[str, Any]:
        """Check telemetry system health"""
        return {
            'sources_active': len(self.gateway.sources),
            'rate_limit_status': {
                src: limiter.get_status()
                for src, limiter in self.gateway.rate_limiters.items()
            },
            'recent_events': self.gateway.get_recent_telemetry(hours=1),
            'errors': self._get_recent_errors(),
            'data_quality': self._assess_quality(),
        }
    
    def _assess_quality(self) -> Dict[str, Any]:
        """Assess telemetry data quality"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT source, COUNT(*) as total, AVG(relevance) as avg_rel
            FROM telemetry
            WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY source
        """)
        
        quality = {}
        for source, total, avg_rel in cursor.fetchall():
            quality[source] = {
                'events': total,
                'avg_relevance': avg_rel,
                'quality_score': avg_rel  # Higher relevance = better quality
            }
        
        conn.close()
        return quality
```

---

## Cost Analysis

| Source | Free Tier | Cost | Requests/day |
|--------|-----------|------|-------------|
| HackerNews | ✅ | $0 | Unlimited |
| Weather | ✅ | $0 | 1000 free |
| RSS/Feeds | ✅ | $0 | Unlimited |
| Google Trends | ✅ | $0 | 100 free |
| NewsAPI | 100/day | $49/mo | 10,000 |
| Alpha Vantage | 5/min | $40+/mo | 500/day |
| CoinGecko | ✅ | $0 | Unlimited |
| Reddit | ✅ | $0 | 1/sec |
| Twitter API | Limited | $100+/mo | Variable |
| **Total Free Tier** | - | **$0** | **~15K+/day** |

You can run production telemetry with **zero cost** using free tiers!

---

## Next Steps

1. **This Week**: Set up Phase 1 (HackerNews, Weather, RSS)
2. **Next Week**: Add one free API (CoinGecko, Google Trends)
3. **Week 3**: Integrate context enrichment
4. **Week 4**: Monitor telemetry influence on decisions
5. **Month 2**: Add premium sources (NewsAPI, AlphaVantage)
6. **Month 3**: Real-time streams (WebSocket, Kafka)

Ready to make The Brain context-aware? 🚀📡
