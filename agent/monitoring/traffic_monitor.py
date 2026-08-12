"""
Traffic Monitor: Analyze web usage patterns
Learn from your browsing and activity to understand interests
"""

import sqlite3
import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path


class TrafficMonitor:
    """Monitor and learn from traffic patterns"""

    def __init__(self, db_path: str = "./agent/storage/memory.db"):
        self.db_path = db_path
        self.interval = int(os.getenv("MONITOR_INTERVAL", "60"))
        self._initialize_tables()

    def _initialize_tables(self):
        """Create traffic tracking tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traffic_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                domain TEXT,
                path TEXT,
                activity_type TEXT,
                duration_seconds INTEGER,
                user_interaction INTEGER,
                category TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traffic_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT,
                domain TEXT,
                frequency INTEGER,
                avg_duration INTEGER,
                peak_hours TEXT,
                importance_score REAL,
                category TEXT,
                last_visit DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS browsing_interests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interest_category TEXT,
                keywords TEXT,
                frequency INTEGER,
                confidence_score REAL,
                last_detected DATETIME
            )
        """)

        conn.commit()
        conn.close()

    def categorize_domain(self, domain: str) -> str:
        """Categorize website by type"""
        categories = {
            "work": ["github", "gitlab", "jira", "confluence", "slack", "teams", "work"],
            "learning": ["github", "stackoverflow", "udemy", "coursera", "medium", "dev.to"],
            "social": ["twitter", "linkedin", "facebook", "instagram", "reddit"],
            "news": ["bbc", "cnn", "reuters", "guardian", "hacker news"],
            "entertainment": ["youtube", "netflix", "twitch", "spotify"],
            "shopping": ["amazon", "ebay", "etsy", "shop"],
            "productivity": ["notion", "asana", "trello", "monday", "airtable"],
            "research": ["google", "bing", "duckduckgo", "scholar", "arxiv"],
        }

        domain_lower = domain.lower()
        for category, keywords in categories.items():
            if any(kw in domain_lower for kw in keywords):
                return category

        return "other"

    def extract_interests(self, domain: str, path: str = "") -> list:
        """Extract interests from browsing activity"""
        interests = []

        # Map domains to topics
        topic_map = {
            "github": ["programming", "coding", "projects"],
            "stackoverflow": ["programming", "debugging"],
            "medium": ["writing", "ideas", "learning"],
            "arxiv": ["research", "papers", "science"],
            "hacker news": ["tech", "startups", "innovation"],
            "youtube": ["video", "learning", "entertainment"],
            "twitter": ["news", "ideas", "discussion"],
            "linkedin": ["career", "professional", "networking"],
        }

        for domain_kw, topics in topic_map.items():
            if domain_kw in domain.lower():
                interests.extend(topics)

        return list(set(interests))

    def log_traffic_activity(self, domain: str, path: str = "", duration: int = 0, user_action: bool = True):
        """Log web traffic activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        category = self.categorize_domain(domain)
        interests = self.extract_interests(domain, path)

        cursor.execute("""
            INSERT INTO traffic_activity
            (timestamp, domain, path, activity_type, duration_seconds, user_interaction, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            domain,
            path,
            "visit",
            duration,
            1 if user_action else 0,
            category
        ))

        # Update browsing interests
        for interest in interests:
            cursor.execute("""
                INSERT INTO browsing_interests (interest_category, keywords, frequency, last_detected)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(interest_category) DO UPDATE SET
                    frequency = frequency + 1,
                    last_detected = ?
            """, (interest, domain, datetime.now().isoformat(), datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def analyze_traffic_patterns(self) -> dict:
        """Analyze browsing patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get top domains
        cursor.execute("""
            SELECT domain, COUNT(*) as visits
            FROM traffic_activity
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY domain
            ORDER BY visits DESC
            LIMIT 10
        """)

        top_domains = [{"domain": row[0], "visits": row[1]} for row in cursor.fetchall()]

        # Get categories
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM traffic_activity
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY category
            ORDER BY count DESC
        """)

        categories = {row[0]: row[1] for row in cursor.fetchall()}

        # Get interests
        cursor.execute("""
            SELECT interest_category, frequency
            FROM browsing_interests
            ORDER BY frequency DESC
            LIMIT 10
        """)

        interests = [{"topic": row[0], "frequency": row[1]} for row in cursor.fetchall()]

        conn.close()

        return {
            "top_domains": top_domains,
            "categories": categories,
            "detected_interests": interests,
            "timestamp": datetime.now().isoformat()
        }

    def run(self):
        """Main monitoring loop"""
        print("🌐 Traffic Monitor started")
        print(f"   Interval: {self.interval}s")
        print("   Note: Requires integration with browser/system monitoring")

        iteration = 0
        try:
            while True:
                iteration += 1
                print(f"\n[{datetime.now().isoformat()}] Checking traffic patterns... (iteration {iteration})")

                try:
                    # Analyze current patterns
                    patterns = self.analyze_traffic_patterns()

                    if patterns["top_domains"]:
                        print(f"✅ Top domains: {[d['domain'] for d in patterns['top_domains'][:3]]}")
                    if patterns["detected_interests"]:
                        print(f"   Interests: {[i['topic'] for i in patterns['detected_interests'][:3]]}")
                    if patterns["categories"]:
                        print(f"   Categories: {patterns['categories']}")

                except Exception as e:
                    print(f"❌ Error analyzing traffic: {e}")

                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\n\n🌐 Traffic Monitor stopped")


if __name__ == "__main__":
    monitor = TrafficMonitor()
    monitor.run()
