"""
Memory: Brain's learning system
Records decisions, learns patterns, improves strategy
10% retention, 3-month destruction policy
"""

import sqlite3
import json
import random
from datetime import datetime, timedelta
from pathlib import Path


class Memory:
    """Persistent learning system"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def initialize(self):
        """Create tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Decisions table (what the Brain decided and the outcome)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                decision_name TEXT,
                decision_data TEXT,
                outcome_text TEXT,
                success BOOLEAN,
                ttl_expires DATETIME
            )
        """)

        # Events table (10% sample for logging)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                event_type TEXT,
                event_data TEXT,
                ttl_expires DATETIME
            )
        """)

        # Patterns table (what works)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT,
                situation TEXT,
                strategy TEXT,
                success_rate REAL,
                examples TEXT,
                learned_at DATETIME
            )
        """)

        # Resources table (cost tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                action_type TEXT,
                cost_usd REAL,
                revenue_usd REAL,
                roi REAL
            )
        """)

        # Ratings table (user feedback on decisions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER,
                rating INTEGER,
                feedback TEXT,
                rated_at DATETIME,
                FOREIGN KEY(decision_id) REFERENCES decisions(id)
            )
        """)

        conn.commit()
        conn.close()
        print("✅ Memory initialized")

    async def record_decision(
        self,
        decision: dict,
        outcome: dict,
        timestamp: datetime = None
    ):
        """Record a decision and its outcome"""
        timestamp = timestamp or datetime.now()

        # 10% sampling (compression)
        if random.random() < 0.1:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Calculate TTL (3 months)
            ttl = timestamp + timedelta(days=90)

            cursor.execute("""
                INSERT INTO decisions
                (timestamp, decision_name, decision_data, outcome_text, success, ttl_expires)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                timestamp.isoformat(),
                decision.get("name", "unknown"),
                json.dumps(decision),
                json.dumps(outcome),
                outcome.get("success", False),
                ttl.isoformat()
            ))

            conn.commit()
            conn.close()

    async def log_event(self, event_type: str, event_data: dict):
        """Log an event (10% sample)"""
        if random.random() < 0.1:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            ttl = datetime.now() + timedelta(days=90)

            cursor.execute("""
                INSERT INTO events
                (timestamp, event_type, event_data, ttl_expires)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                event_type,
                json.dumps(event_data),
                ttl.isoformat()
            ))

            conn.commit()
            conn.close()

    def get_recent_decisions(self, hours: int = 24) -> list:
        """Get recent decisions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        cursor.execute("""
            SELECT decision_name, outcome_text, success, timestamp
            FROM decisions
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        """, (cutoff,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "name": row[0],
                "outcome": json.loads(row[1]) if row[1] else {},
                "success": row[2],
                "timestamp": row[3]
            })

        conn.close()
        return results

    def get_monthly_spend(self) -> float:
        """Get spending this month"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        month_ago = (datetime.now() - timedelta(days=30)).isoformat()

        cursor.execute("""
            SELECT SUM(cost_usd) FROM resources WHERE timestamp > ?
        """, (month_ago,))

        result = cursor.fetchone()[0] or 0.0
        conn.close()
        return result

    def count_patterns(self) -> int:
        """Count learned patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM patterns")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def count_events(self) -> int:
        """Count logged events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM events")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    async def cleanup_expired(self):
        """Delete events older than 3 months"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("DELETE FROM events WHERE ttl_expires < ?", (now,))
        cursor.execute("DELETE FROM decisions WHERE ttl_expires < ?", (now,))

        conn.commit()
        conn.close()

    def rate_decision(self, decision_id: int, rating: int, feedback: str = ""):
        """Rate a decision (1-5 scale)"""
        if not 1 <= rating <= 5:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ratings (decision_id, rating, feedback, rated_at)
            VALUES (?, ?, ?, ?)
        """, (decision_id, rating, feedback, datetime.now().isoformat()))

        conn.commit()
        conn.close()
        return True

    def get_unrated_decisions(self, limit: int = 10) -> list:
        """Get decisions waiting for user feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT d.id, d.decision_name, d.decision_data, d.timestamp
            FROM decisions d
            LEFT JOIN ratings r ON d.id = r.decision_id
            WHERE r.id IS NULL
            ORDER BY d.timestamp DESC
            LIMIT ?
        """, (limit,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "name": row[1],
                "decision": json.loads(row[2]) if row[2] else {},
                "timestamp": row[3]
            })

        conn.close()
        return results

    def extract_patterns(self) -> list:
        """Find patterns in rated decisions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get decisions with ratings
        cursor.execute("""
            SELECT d.decision_name, d.decision_data, r.rating
            FROM decisions d
            JOIN ratings r ON d.id = r.decision_id
            ORDER BY d.timestamp DESC
            LIMIT 100
        """)

        decisions = cursor.fetchall()
        conn.close()

        if not decisions:
            return []

        # Group by decision name, calculate success rate
        patterns = {}
        for name, data, rating in decisions:
            if name not in patterns:
                patterns[name] = {"total": 0, "good": 0, "ratings": []}

            patterns[name]["total"] += 1
            patterns[name]["ratings"].append(rating)
            if rating >= 4:
                patterns[name]["good"] += 1

        # Convert to pattern list
        result = []
        for name, stats in sorted(patterns.items(), key=lambda x: x[1]["good"] / max(x[1]["total"], 1), reverse=True):
            success_rate = stats["good"] / max(stats["total"], 1)
            result.append({
                "name": name,
                "success_rate": success_rate,
                "total_uses": stats["total"],
                "good_uses": stats["good"],
                "avg_rating": sum(stats["ratings"]) / len(stats["ratings"])
            })

        return result

    def get_confidence(self, decision_name: str) -> float:
        """Get confidence level for a decision type (0-1)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) as total, SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) as good
            FROM ratings r
            JOIN decisions d ON r.decision_id = d.id
            WHERE d.decision_name = ?
        """, (decision_name,))

        result = cursor.fetchone()
        conn.close()

        if not result or result[0] == 0:
            return 0.5  # Default neutral confidence

        total, good = result
        return min(1.0, good / max(total, 1))
