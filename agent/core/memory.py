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
