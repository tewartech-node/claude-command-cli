"""
Diagnostic Engine: Routine Health Scans
Monitors system state, detects anomalies, identifies performance issues
"""

import sqlite3
import psutil
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import os


class DiagnosticEngine:
    """Runs routine diagnostic scans on the system"""

    def __init__(self, db_path: str = "./agent/storage/memory.db", scan_interval: int = 300):
        self.db_path = db_path
        self.scan_interval = scan_interval  # seconds
        self.diagnostics_dir = Path("./agent/storage/diagnostics")
        self.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        self._init_diagnostics_table()

    def _init_diagnostics_table(self):
        """Initialize diagnostics tracking table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnostics (
                id INTEGER PRIMARY KEY,
                scan_timestamp TEXT,
                scan_type TEXT,
                severity TEXT,
                category TEXT,
                issue TEXT,
                details TEXT,
                resolved INTEGER DEFAULT 0,
                resolution_timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    def full_diagnostic_scan(self) -> Dict[str, Any]:
        """Execute complete system diagnostic scan"""
        scan_time = datetime.now().isoformat()
        issues = []

        # Performance diagnostics
        perf_issues = self._scan_performance()
        issues.extend(perf_issues)

        # Code health diagnostics
        code_issues = self._scan_code_health()
        issues.extend(code_issues)

        # Database diagnostics
        db_issues = self._scan_database()
        issues.extend(db_issues)

        # Memory diagnostics
        mem_issues = self._scan_memory()
        issues.extend(mem_issues)

        # Decision quality diagnostics
        quality_issues = self._scan_decision_quality()
        issues.extend(quality_issues)

        # Learning diagnostics
        learning_issues = self._scan_learning_health()
        issues.extend(learning_issues)

        # Network diagnostics
        net_issues = self._scan_network()
        issues.extend(net_issues)

        # Store scan results
        for issue in issues:
            self._log_diagnostic(issue)

        return {
            "scan_timestamp": scan_time,
            "total_issues": len(issues),
            "critical": len([i for i in issues if i["severity"] == "CRITICAL"]),
            "warning": len([i for i in issues if i["severity"] == "WARNING"]),
            "info": len([i for i in issues if i["severity"] == "INFO"]),
            "issues": issues,
        }

    def _scan_performance(self) -> List[Dict[str, Any]]:
        """Scan for performance issues"""
        issues = []
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                issues.append({
                    "severity": "WARNING",
                    "category": "performance",
                    "issue": f"High CPU usage: {cpu_percent}%",
                    "details": "CPU utilization exceeds 80%",
                })

            # Memory usage
            mem = psutil.virtual_memory()
            if mem.percent > 85:
                issues.append({
                    "severity": "CRITICAL",
                    "category": "performance",
                    "issue": f"Memory pressure: {mem.percent}% used",
                    "details": f"Available: {mem.available / 1024**3:.1f}GB, Used: {mem.used / 1024**3:.1f}GB",
                })

            # Disk usage
            disk = psutil.disk_usage("/")
            if disk.percent > 90:
                issues.append({
                    "severity": "CRITICAL",
                    "category": "performance",
                    "issue": f"Low disk space: {disk.percent}% used",
                    "details": f"Free space: {disk.free / 1024**3:.1f}GB",
                })

        except Exception as e:
            issues.append({
                "severity": "WARNING",
                "category": "performance",
                "issue": "Performance monitoring failed",
                "details": str(e),
            })

        return issues

    def _scan_code_health(self) -> List[Dict[str, Any]]:
        """Scan for code quality issues"""
        issues = []
        try:
            # Check for dead code (imports that aren't used)
            # Check for circular dependencies
            # Check for proper error handling
            # This would be enhanced with static analysis tools

            agent_dir = Path("./agent")
            py_files = list(agent_dir.glob("**/*.py"))

            if not py_files:
                issues.append({
                    "severity": "WARNING",
                    "category": "code_health",
                    "issue": "No Python files found in agent directory",
                    "details": "Code base may be corrupted or misconfigured",
                })

        except Exception as e:
            issues.append({
                "severity": "WARNING",
                "category": "code_health",
                "issue": "Code health scan failed",
                "details": str(e),
            })

        return issues

    def _scan_database(self) -> List[Dict[str, Any]]:
        """Scan database integrity and performance"""
        issues = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check database integrity
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            if integrity != "ok":
                issues.append({
                    "severity": "CRITICAL",
                    "category": "database",
                    "issue": "Database integrity check failed",
                    "details": integrity,
                })

            # Check table sizes
            cursor.execute("""
                SELECT name, (page_count * page_size) as size
                FROM pragma_page_count(), pragma_page_size()
            """)
            db_size = cursor.fetchone()
            if db_size and db_size[1] > 500 * 1024 * 1024:  # 500MB
                issues.append({
                    "severity": "WARNING",
                    "category": "database",
                    "issue": f"Large database: {db_size[1] / 1024 / 1024:.1f}MB",
                    "details": "Consider vacuuming or archiving old data",
                })

            # Check for fragmentation
            cursor.execute("PRAGMA freelist_count")
            freelist = cursor.fetchone()[0]
            if freelist > 1000:
                issues.append({
                    "severity": "INFO",
                    "category": "database",
                    "issue": f"Database fragmentation: {freelist} free pages",
                    "details": "VACUUM would optimize performance",
                })

            conn.close()

        except Exception as e:
            issues.append({
                "severity": "WARNING",
                "category": "database",
                "issue": "Database scan failed",
                "details": str(e),
            })

        return issues

    def _scan_memory(self) -> List[Dict[str, Any]]:
        """Scan for memory leaks and unusual patterns"""
        issues = []
        try:
            # Check if process is consuming excessive memory
            process = psutil.Process()
            mem_info = process.memory_info()
            mem_mb = mem_info.rss / 1024 / 1024

            if mem_mb > 500:  # > 500MB
                issues.append({
                    "severity": "WARNING",
                    "category": "memory",
                    "issue": f"High memory consumption: {mem_mb:.1f}MB",
                    "details": "Potential memory leak or large data structures",
                })

        except Exception as e:
            issues.append({
                "severity": "INFO",
                "category": "memory",
                "issue": "Memory scan failed",
                "details": str(e),
            })

        return issues

    def _scan_decision_quality(self) -> List[Dict[str, Any]]:
        """Scan decision quality metrics"""
        issues = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check success rate
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                FROM decisions
                WHERE timestamp > datetime('now', '-24 hours')
            """)
            total, successful = cursor.fetchone()

            if total > 0:
                success_rate = (successful / total) * 100
                if success_rate < 50:
                    issues.append({
                        "severity": "CRITICAL",
                        "category": "decision_quality",
                        "issue": f"Low success rate: {success_rate:.1f}% (24h)",
                        "details": f"{successful}/{total} decisions successful",
                    })
                elif success_rate < 70:
                    issues.append({
                        "severity": "WARNING",
                        "category": "decision_quality",
                        "issue": f"Below-target success rate: {success_rate:.1f}%",
                        "details": "Expected >85% after learning",
                    })

            # Check for unrated decisions
            cursor.execute("""
                SELECT COUNT(*) FROM decisions WHERE id NOT IN (
                    SELECT DISTINCT decision_id FROM ratings
                ) AND timestamp > datetime('now', '-7 days')
            """)
            unrated = cursor.fetchone()[0]
            if unrated > 100:
                issues.append({
                    "severity": "WARNING",
                    "category": "decision_quality",
                    "issue": f"Many unrated decisions: {unrated}",
                    "details": "Ratings improve learning; consider rating recent decisions",
                })

            conn.close()

        except Exception as e:
            issues.append({
                "severity": "INFO",
                "category": "decision_quality",
                "issue": "Decision quality scan failed",
                "details": str(e),
            })

        return issues

    def _scan_learning_health(self) -> List[Dict[str, Any]]:
        """Scan learning progress and patterns"""
        issues = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check pattern count
            cursor.execute("SELECT COUNT(*) FROM patterns")
            patterns = cursor.fetchone()[0]

            if patterns == 0:
                issues.append({
                    "severity": "WARNING",
                    "category": "learning",
                    "issue": "No patterns learned yet",
                    "details": "System needs more data or is not analyzing properly",
                })

            # Check confidence levels
            cursor.execute("""
                SELECT AVG(confidence) as avg_conf FROM patterns
            """)
            avg_conf = cursor.fetchone()[0]
            if avg_conf and avg_conf < 0.5:
                issues.append({
                    "severity": "WARNING",
                    "category": "learning",
                    "issue": f"Low average confidence: {avg_conf:.2f}",
                    "details": "Patterns may be weak or noisy",
                })

            conn.close()

        except Exception as e:
            issues.append({
                "severity": "INFO",
                "category": "learning",
                "issue": "Learning health scan failed",
                "details": str(e),
            })

        return issues

    def _scan_network(self) -> List[Dict[str, Any]]:
        """Scan network connectivity and API health"""
        issues = []
        try:
            # Check network connectivity
            import socket
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=3)
            except (socket.timeout, socket.error):
                issues.append({
                    "severity": "CRITICAL",
                    "category": "network",
                    "issue": "Network connectivity lost",
                    "details": "Cannot reach external networks",
                })

        except Exception as e:
            issues.append({
                "severity": "INFO",
                "category": "network",
                "issue": "Network scan failed",
                "details": str(e),
            })

        return issues

    def _log_diagnostic(self, issue: Dict[str, Any]):
        """Log a diagnostic issue to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO diagnostics
            (scan_timestamp, scan_type, severity, category, issue, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "routine",
            issue["severity"],
            issue["category"],
            issue["issue"],
            json.dumps(issue.get("details", "")),
        ))
        conn.commit()
        conn.close()

    def get_recent_diagnostics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get diagnostics from last N hours"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff = datetime.now() - timedelta(hours=hours)
        cursor.execute("""
            SELECT * FROM diagnostics
            WHERE scan_timestamp > ?
            ORDER BY scan_timestamp DESC
        """, (cutoff.isoformat(),))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_critical_issues(self) -> List[Dict[str, Any]]:
        """Get all unresolved critical issues"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM diagnostics
            WHERE severity = 'CRITICAL' AND resolved = 0
            ORDER BY scan_timestamp DESC
        """)

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def mark_resolved(self, diagnostic_id: int):
        """Mark a diagnostic issue as resolved"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE diagnostics
            SET resolved = 1, resolution_timestamp = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), diagnostic_id))
        conn.commit()
        conn.close()
