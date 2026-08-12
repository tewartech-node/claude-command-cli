"""
Sync: Cross-device memory synchronization
Allows arrdee and git to share decision history and patterns
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path


class MemorySync:
    """Synchronize memory across devices"""

    def __init__(self, db_path: str, device_name: str = "unknown"):
        self.db_path = db_path
        self.device_name = device_name
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def export_decisions(self, since: str = None) -> list:
        """Export decisions for sync (since timestamp if provided)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if since:
            query = """
                SELECT id, timestamp, decision_name, decision_data, outcome_text, success, ttl_expires
                FROM decisions
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """
            cursor.execute(query, (since,))
        else:
            query = """
                SELECT id, timestamp, decision_name, decision_data, outcome_text, success, ttl_expires
                FROM decisions
                ORDER BY timestamp DESC
                LIMIT 100
            """
            cursor.execute(query)

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "timestamp": row[1],
                "decision_name": row[2],
                "decision_data": json.loads(row[3]) if row[3] else {},
                "outcome_text": json.loads(row[4]) if row[4] else {},
                "success": bool(row[5]),
                "ttl_expires": row[6],
                "source_device": self.device_name
            })

        conn.close()
        return results

    def export_ratings(self, since: str = None) -> list:
        """Export ratings for sync"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if since:
            query = """
                SELECT decision_id, rating, feedback, rated_at
                FROM ratings
                WHERE rated_at > ?
                ORDER BY rated_at DESC
            """
            cursor.execute(query, (since,))
        else:
            query = """
                SELECT decision_id, rating, feedback, rated_at
                FROM ratings
                ORDER BY rated_at DESC
                LIMIT 100
            """
            cursor.execute(query)

        results = []
        for row in cursor.fetchall():
            results.append({
                "decision_id": row[0],
                "rating": row[1],
                "feedback": row[2],
                "rated_at": row[3]
            })

        conn.close()
        return results

    def export_patterns(self) -> list:
        """Export learned patterns for sync"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT pattern_name, situation, strategy, success_rate, examples, learned_at
            FROM patterns
            ORDER BY learned_at DESC
        """)

        results = []
        for row in cursor.fetchall():
            results.append({
                "pattern_name": row[0],
                "situation": row[1],
                "strategy": row[2],
                "success_rate": row[3],
                "examples": json.loads(row[4]) if row[4] else [],
                "learned_at": row[5],
                "source_device": self.device_name
            })

        conn.close()
        return results

    def generate_sync_checksum(self) -> str:
        """Generate checksum of current state for verification"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get hash of recent decisions and ratings
        cursor.execute("SELECT COUNT(*), SUM(id) FROM decisions")
        d_count, d_sum = cursor.fetchone()

        cursor.execute("SELECT COUNT(*), SUM(id) FROM ratings")
        r_count, r_sum = cursor.fetchone()

        state = f"{d_count}:{d_sum}:{r_count}:{r_sum}"
        conn.close()

        return hashlib.sha256(state.encode()).hexdigest()[:8]

    def get_sync_status(self) -> dict:
        """Get status for sync reporting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM decisions")
        decisions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM ratings")
        ratings = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM patterns")
        patterns = cursor.fetchone()[0]

        conn.close()

        return {
            "device": self.device_name,
            "decisions_total": decisions,
            "ratings_total": ratings,
            "patterns_total": patterns,
            "last_sync": datetime.now().isoformat(),
            "checksum": self.generate_sync_checksum()
        }
