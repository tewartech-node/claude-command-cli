"""
Behavior Monitor: Continuous System Monitoring
Tracks performance, detects anomalies, triggers alerts
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Callable, Optional
from pathlib import Path
import sqlite3
import threading


class BehaviorMonitor:
    """Continuously monitors system behavior and health"""

    def __init__(self, db_path: str = "./agent/storage/memory.db", alert_threshold: float = 0.7):
        self.db_path = db_path
        self.alert_threshold = alert_threshold
        self.metrics = {}
        self.baseline = {}
        self.alerts = []
        self.is_running = False
        self.monitoring_thread = None
        self._init_monitoring_tables()
        self._load_baseline()

    def _init_monitoring_tables(self):
        """Initialize monitoring data tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS behavior_metrics (
                id INTEGER PRIMARY KEY,
                metric_timestamp TEXT,
                metric_name TEXT,
                metric_value REAL,
                category TEXT,
                expected_value REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY,
                alert_timestamp TEXT,
                alert_type TEXT,
                severity TEXT,
                metric_name TEXT,
                metric_value REAL,
                threshold REAL,
                message TEXT,
                acknowledged INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

    def _load_baseline(self):
        """Load historical baseline for anomaly detection"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Calculate baseline metrics from last 7 days
            cursor.execute("""
                SELECT metric_name, AVG(metric_value)
                FROM behavior_metrics
                WHERE metric_timestamp > datetime('now', '-7 days')
                GROUP BY metric_name
            """)

            for metric_name, avg_value in cursor.fetchall():
                self.baseline[metric_name] = avg_value

            conn.close()

        except Exception as e:
            pass

    def start_monitoring(self):
        """Start continuous monitoring in background"""
        if self.is_running:
            return

        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

    def _monitor_loop(self):
        """Main monitoring loop runs every 60 seconds"""
        while self.is_running:
            try:
                self.collect_metrics()
                self.detect_anomalies()
                time.sleep(60)  # Check every minute
            except Exception as e:
                pass

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        metrics = {}

        # Success rate (last 24h)
        metrics["success_rate_24h"] = self._get_success_rate(24)

        # Average confidence
        metrics["avg_confidence"] = self._get_avg_confidence()

        # Decision velocity (decisions per hour)
        metrics["decision_velocity"] = self._get_decision_velocity()

        # Email processing rate
        metrics["email_processing_rate"] = self._get_email_processing_rate()

        # Pattern extraction rate
        metrics["pattern_extraction_rate"] = self._get_pattern_extraction_rate()

        # Memory usage prediction
        metrics["memory_trend"] = self._get_memory_trend()

        # Response time (decision latency)
        metrics["response_latency"] = self._get_response_latency()

        # Error rate
        metrics["error_rate"] = self._get_error_rate()

        self.metrics = metrics
        self._store_metrics(metrics)

        return metrics

    def _get_success_rate(self, hours: int) -> float:
        """Get success rate for last N hours"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                FROM decisions
                WHERE timestamp > datetime('now', ? || ' hours')
            """, (f"-{hours}",))

            total, successful = cursor.fetchone()
            conn.close()

            return (successful / total * 100) if total > 0 else 50.0

        except Exception:
            return 50.0

    def _get_avg_confidence(self) -> float:
        """Get average decision confidence"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT AVG(confidence) FROM patterns
                WHERE timestamp > datetime('now', '-7 days')
            """)

            result = cursor.fetchone()[0]
            conn.close()

            return result if result else 0.5

        except Exception:
            return 0.5

    def _get_decision_velocity(self) -> float:
        """Get decisions per hour"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM decisions
                WHERE timestamp > datetime('now', '-1 hours')
            """)

            count = cursor.fetchone()[0]
            conn.close()

            return float(count)

        except Exception:
            return 0.0

    def _get_email_processing_rate(self) -> float:
        """Get emails processed per hour"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM email_activity
                WHERE timestamp > datetime('now', '-1 hours')
            """)

            count = cursor.fetchone()[0]
            conn.close()

            return float(count)

        except Exception:
            return 0.0

    def _get_pattern_extraction_rate(self) -> float:
        """Get patterns extracted per day"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM patterns
                WHERE timestamp > datetime('now', '-1 days')
            """)

            count = cursor.fetchone()[0]
            conn.close()

            return float(count) / 24.0  # Per hour

        except Exception:
            return 0.0

    def _get_memory_trend(self) -> str:
        """Get memory usage trend"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT metric_value
                FROM behavior_metrics
                WHERE metric_name = 'memory_usage'
                ORDER BY metric_timestamp DESC
                LIMIT 10
            """)

            values = [row[0] for row in cursor.fetchall()]
            conn.close()

            if len(values) < 2:
                return "stable"

            recent = values[0]
            previous = values[-1]

            if recent > previous * 1.2:
                return "increasing"
            elif recent < previous * 0.8:
                return "decreasing"
            else:
                return "stable"

        except Exception:
            return "unknown"

    def _get_response_latency(self) -> float:
        """Get average decision latency"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Simplified: return 0 as baseline, real implementation would measure
            conn.close()
            return 0.0

        except Exception:
            return 0.0

    def _get_error_rate(self) -> float:
        """Get error rate from diagnostics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM diagnostics
                WHERE severity IN ('CRITICAL', 'WARNING')
                AND scan_timestamp > datetime('now', '-1 hours')
            """)

            errors = cursor.fetchone()[0]
            conn.close()

            return float(errors)

        except Exception:
            return 0.0

    def _store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for metric_name, metric_value in metrics.items():
            if isinstance(metric_value, (int, float)):
                cursor.execute("""
                    INSERT INTO behavior_metrics
                    (metric_timestamp, metric_name, metric_value, category)
                    VALUES (?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    metric_name,
                    metric_value,
                    "system",
                ))

        conn.commit()
        conn.close()

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies in metrics"""
        anomalies = []

        for metric_name, current_value in self.metrics.items():
            if metric_name not in self.baseline:
                continue

            baseline_value = self.baseline[metric_name]

            # Calculate deviation
            if baseline_value > 0:
                deviation = abs(current_value - baseline_value) / baseline_value
            else:
                deviation = 0

            # Alert if deviation > threshold
            if deviation > self.alert_threshold:
                anomalies.append({
                    "metric": metric_name,
                    "baseline": baseline_value,
                    "current": current_value,
                    "deviation": deviation,
                    "severity": "high" if deviation > 0.5 else "medium",
                })

                self._create_alert(metric_name, current_value, baseline_value)

        return anomalies

    def _create_alert(self, metric_name: str, current_value: float, threshold: float):
        """Create and store an alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alerts
            (alert_timestamp, alert_type, severity, metric_name, metric_value, threshold, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "anomaly_detection",
            "high" if current_value > threshold * 1.5 else "medium",
            metric_name,
            current_value,
            threshold,
            f"{metric_name} deviating from baseline: {current_value:.2f} vs {threshold:.2f}",
        ))

        conn.commit()
        conn.close()

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all unacknowledged alerts"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM alerts
            WHERE acknowledged = 0
            ORDER BY alert_timestamp DESC
        """)

        alerts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return alerts

    def acknowledge_alert(self, alert_id: int):
        """Mark an alert as acknowledged"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE alerts SET acknowledged = 1 WHERE id = ?
        """, (alert_id,))

        conn.commit()
        conn.close()

    def get_health_score(self) -> float:
        """Calculate overall system health score (0-100)"""
        score = 100.0

        # Deduct for low success rate
        success_rate = self.metrics.get("success_rate_24h", 50)
        if success_rate < 70:
            score -= (70 - success_rate) / 70 * 20

        # Deduct for low confidence
        confidence = self.metrics.get("avg_confidence", 0.5)
        if confidence < 0.7:
            score -= (0.7 - confidence) * 20

        # Deduct for high error rate
        errors = self.metrics.get("error_rate", 0)
        if errors > 5:
            score -= min(20, errors)

        return max(0, min(100, score))

    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "health_score": self.get_health_score(),
            "metrics": self.metrics,
            "active_alerts": len(self.get_active_alerts()),
            "anomalies_detected": self.detect_anomalies(),
            "is_monitoring": self.is_running,
        }
