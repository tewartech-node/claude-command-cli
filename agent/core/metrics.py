"""
Metrics: Performance tracking and analytics
Measures decision quality, success rates, and learning progress
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


class Metrics:
    """Track Brain performance and learning"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def initialize(self):
        """Create metrics tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                metric_name TEXT,
                value REAL,
                decision_id INTEGER,
                FOREIGN KEY(decision_id) REFERENCES decisions(id)
            )
        """)

        conn.commit()
        conn.close()

    def get_success_rate(self, hours: int = 24) -> float:
        """Get success rate for recent decisions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        cursor.execute("""
            SELECT COUNT(*) as total, SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes
            FROM decisions
            WHERE timestamp > ?
        """, (cutoff,))

        result = cursor.fetchone()
        conn.close()

        if not result or result[0] == 0:
            return 0.0

        total, successes = result
        return (successes / total) * 100

    def get_top_decisions(self, limit: int = 10) -> list:
        """Get highest-confidence decision types"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT d.decision_name, COUNT(*) as uses,
                   SUM(CASE WHEN r.rating >= 4 THEN 1 ELSE 0 END) as good_ratings,
                   AVG(CASE WHEN r.rating IS NOT NULL THEN r.rating ELSE 0 END) as avg_rating
            FROM decisions d
            LEFT JOIN ratings r ON d.id = r.decision_id
            GROUP BY d.decision_name
            ORDER BY good_ratings DESC, uses DESC
            LIMIT ?
        """, (limit,))

        results = []
        for row in cursor.fetchall():
            name, uses, good, avg = row
            results.append({
                "decision": name,
                "uses": uses,
                "good_ratings": good or 0,
                "avg_rating": round(avg, 2) if avg else 0,
                "success_rate": round((good / uses * 100) if uses > 0 else 0, 1)
            })

        conn.close()
        return results

    def get_daily_stats(self, days: int = 7) -> list:
        """Get statistics for last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        results = []
        for i in range(days):
            day = datetime.now() - timedelta(days=i)
            start = day.replace(hour=0, minute=0, second=0).isoformat()
            end = day.replace(hour=23, minute=59, second=59).isoformat()

            cursor.execute("""
                SELECT COUNT(*) as total, SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes
                FROM decisions
                WHERE timestamp BETWEEN ? AND ?
            """, (start, end))

            row = cursor.fetchone()
            total, successes = row if row else (0, 0)

            results.append({
                "date": day.strftime("%Y-%m-%d"),
                "decisions_made": total,
                "successful": successes or 0,
                "success_rate": round((successes / total * 100) if total > 0 else 0, 1)
            })

        conn.close()
        return results

    def get_learning_progress(self) -> dict:
        """Get overall learning progress"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total decisions made
        cursor.execute("SELECT COUNT(*) FROM decisions")
        total_decisions = cursor.fetchone()[0]

        # Rated decisions
        cursor.execute("SELECT COUNT(DISTINCT decision_id) FROM ratings")
        rated_decisions = cursor.fetchone()[0]

        # Patterns learned
        cursor.execute("SELECT COUNT(*) FROM patterns")
        patterns = cursor.fetchone()[0]

        # Average rating
        cursor.execute("SELECT AVG(rating) FROM ratings")
        avg_rating = cursor.fetchone()[0] or 0

        # Overall success rate
        cursor.execute("""
            SELECT SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes
            FROM decisions
        """)
        successes = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "total_decisions": total_decisions,
            "rated_decisions": rated_decisions,
            "feedback_percentage": round((rated_decisions / total_decisions * 100) if total_decisions > 0 else 0, 1),
            "patterns_learned": patterns,
            "avg_rating": round(avg_rating, 2),
            "overall_success_rate": round((successes / total_decisions * 100) if total_decisions > 0 else 0, 1)
        }

    def get_confidence_breakdown(self) -> list:
        """Get confidence levels across decision types"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT d.decision_name,
                   COUNT(*) as total,
                   SUM(CASE WHEN r.rating >= 4 THEN 1 ELSE 0 END) as good,
                   AVG(r.rating) as avg_rating
            FROM decisions d
            LEFT JOIN ratings r ON d.id = r.decision_id
            WHERE r.id IS NOT NULL
            GROUP BY d.decision_name
            ORDER BY good DESC
        """)

        results = []
        for row in cursor.fetchall():
            name, total, good, avg = row
            confidence = (good / total) if total > 0 else 0.5
            results.append({
                "decision_type": name,
                "confidence": round(confidence, 2),
                "total_uses": total,
                "successful_uses": good or 0,
                "avg_rating": round(avg, 2) if avg else 0
            })

        conn.close()
        return results
