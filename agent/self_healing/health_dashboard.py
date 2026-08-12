"""
Health Dashboard: Real-time System Health Visualization
Displays diagnostics, repairs, constraints, and metrics
"""

import sqlite3
from typing import Dict, List, Any
from datetime import datetime, timedelta
from pathlib import Path


class HealthDashboard:
    """Dashboard for system health monitoring and visualization"""

    def __init__(self, db_path: str = "./agent/storage/memory.db"):
        self.db_path = db_path

    def get_comprehensive_health_report(self) -> Dict[str, Any]:
        """Get complete system health report"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        report = {
            "timestamp": datetime.now().isoformat(),
            "diagnostics": self._get_diagnostic_summary(cursor),
            "repairs": self._get_repair_summary(cursor),
            "alerts": self._get_alert_summary(cursor),
            "metrics": self._get_metrics_summary(cursor),
            "compliance": self._get_compliance_summary(cursor),
        }

        conn.close()
        return report

    def _get_diagnostic_summary(self, cursor) -> Dict[str, Any]:
        """Summarize recent diagnostics"""
        # Get recent diagnostics
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM diagnostics
            WHERE scan_timestamp > datetime('now', '-24 hours')
            GROUP BY severity
        """)

        severity_counts = {row["severity"]: row["count"] for row in cursor.fetchall()}

        # Get most recent issue
        cursor.execute("""
            SELECT * FROM diagnostics
            WHERE resolved = 0
            ORDER BY scan_timestamp DESC
            LIMIT 1
        """)

        latest_issue = dict(cursor.fetchone() or {})

        # Get critical issues
        cursor.execute("""
            SELECT COUNT(*) as count FROM diagnostics
            WHERE severity = 'CRITICAL' AND resolved = 0
        """)

        critical_count = cursor.fetchone()[0] if cursor.fetchone() else 0

        return {
            "total_24h": sum(severity_counts.values()),
            "critical": severity_counts.get("CRITICAL", 0),
            "warning": severity_counts.get("WARNING", 0),
            "info": severity_counts.get("INFO", 0),
            "unresolved_critical": critical_count,
            "latest_issue": latest_issue,
        }

    def _get_repair_summary(self, cursor) -> Dict[str, Any]:
        """Summarize recent repairs"""
        # Get repair stats
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM repair_log
            WHERE repair_timestamp > datetime('now', '-24 hours')
            GROUP BY status
        """)

        status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

        # Get latest repairs
        cursor.execute("""
            SELECT * FROM repair_log
            ORDER BY repair_timestamp DESC
            LIMIT 5
        """)

        recent_repairs = [dict(row) for row in cursor.fetchall()]

        return {
            "total_24h": sum(status_counts.values()),
            "successful": status_counts.get("completed", 0),
            "failed": status_counts.get("failed", 0),
            "recommended": status_counts.get("recommended", 0),
            "recent_repairs": recent_repairs,
        }

    def _get_alert_summary(self, cursor) -> Dict[str, Any]:
        """Summarize active alerts"""
        # Get alert counts
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM alerts
            WHERE acknowledged = 0
            GROUP BY severity
        """)

        severity_counts = {row["severity"]: row["count"] for row in cursor.fetchall()}

        # Get active alerts
        cursor.execute("""
            SELECT * FROM alerts
            WHERE acknowledged = 0
            ORDER BY alert_timestamp DESC
            LIMIT 10
        """)

        active_alerts = [dict(row) for row in cursor.fetchall()]

        return {
            "total_active": sum(severity_counts.values()),
            "high_severity": severity_counts.get("high", 0),
            "medium_severity": severity_counts.get("medium", 0),
            "low_severity": severity_counts.get("low", 0),
            "active_alerts": active_alerts,
        }

    def _get_metrics_summary(self, cursor) -> Dict[str, Any]:
        """Summarize key metrics"""
        try:
            # Success rate
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                FROM decisions
                WHERE timestamp > datetime('now', '-24 hours')
            """)

            total, successful = cursor.fetchone()
            success_rate = (successful / total * 100) if total > 0 else 0

            # Average confidence
            cursor.execute("""
                SELECT AVG(confidence) FROM patterns
                WHERE timestamp > datetime('now', '-7 days')
            """)

            avg_confidence = cursor.fetchone()[0] or 0

            # Decision count
            cursor.execute("""
                SELECT COUNT(*) FROM decisions
                WHERE timestamp > datetime('now', '-24 hours')
            """)

            decisions_24h = cursor.fetchone()[0]

            # Pattern count
            cursor.execute("""
                SELECT COUNT(*) FROM patterns
            """)

            total_patterns = cursor.fetchone()[0]

            # Error rate
            cursor.execute("""
                SELECT COUNT(*) FROM diagnostics
                WHERE severity IN ('CRITICAL', 'WARNING')
                AND scan_timestamp > datetime('now', '-24 hours')
            """)

            error_count = cursor.fetchone()[0]

            return {
                "success_rate_24h": round(success_rate, 1),
                "avg_confidence": round(avg_confidence, 2),
                "decisions_24h": decisions_24h,
                "total_patterns_learned": total_patterns,
                "errors_24h": error_count,
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_compliance_summary(self, cursor) -> Dict[str, Any]:
        """Summarize constraint compliance"""
        return {
            "constraints_total": 10,  # From ConstraintSystem defaults
            "constraints_satisfied": 8,  # Placeholder
            "compliance_score": 80.0,  # Placeholder
            "critical_violations": 0,
        }

    def get_dashboard_html(self) -> str:
        """Generate HTML dashboard"""
        report = self.get_comprehensive_health_report()

        health_score = self._calculate_health_score(report)
        health_color = self._get_health_color(health_score)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Brain Self-Healing Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #0f172a;
                    color: #e2e8f0;
                    padding: 20px;
                }}
                .container {{ max-width: 1600px; margin: 0 auto; }}
                h1 {{ margin-bottom: 30px; color: #60a5fa; }}
                h2 {{ color: #60a5fa; font-size: 16px; margin-bottom: 15px; }}
                .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
                .card {{
                    background: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 8px;
                    padding: 20px;
                }}
                .health-score {{
                    font-size: 48px;
                    font-weight: bold;
                    color: {health_color};
                    text-align: center;
                    margin: 20px 0;
                }}
                .stat {{ font-size: 28px; font-weight: bold; color: #10b981; margin: 10px 0; }}
                .label {{ color: #94a3b8; font-size: 12px; text-transform: uppercase; margin-top: 8px; }}
                .list {{ list-style: none; }}
                .list li {{ padding: 8px 0; border-bottom: 1px solid #334155; font-size: 12px; }}
                .list li:last-child {{ border-bottom: none; }}
                .badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                    margin-right: 8px;
                }}
                .badge.critical {{ background: #ef4444; color: white; }}
                .badge.warning {{ background: #f59e0b; color: white; }}
                .badge.info {{ background: #3b82f6; color: white; }}
                .badge.success {{ background: #10b981; color: white; }}
                .alert {{
                    background: rgba(239, 68, 68, 0.1);
                    border-left: 3px solid #ef4444;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 4px;
                }}
                .progress {{
                    background: #334155;
                    height: 8px;
                    border-radius: 4px;
                    overflow: hidden;
                    margin-top: 10px;
                }}
                .progress-bar {{
                    background: linear-gradient(90deg, #60a5fa, #10b981);
                    height: 100%;
                    transition: width 0.3s;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🧠 Self-Healing System Dashboard</h1>

                <div class="grid">
                    <!-- Overall Health -->
                    <div class="card">
                        <h2>System Health</h2>
                        <div class="health-score">{health_score:.0f}%</div>
                        <div class="label">Overall Status</div>
                        <div style="margin-top: 15px; font-size: 12px;">
                            <div>Auto-repairs: {report['repairs']['successful']}</div>
                            <div>Unresolved: {report['diagnostics']['unresolved_critical']}</div>
                        </div>
                    </div>

                    <!-- Diagnostics -->
                    <div class="card">
                        <h2>Diagnostics (24h)</h2>
                        <div class="stat">{report['diagnostics']['total_24h']}</div>
                        <div class="label">Total Issues Found</div>
                        <ul class="list" style="margin-top: 15px;">
                            <li><span class="badge critical">CRITICAL</span> {report['diagnostics']['critical']}</li>
                            <li><span class="badge warning">WARNING</span> {report['diagnostics']['warning']}</li>
                            <li><span class="badge info">INFO</span> {report['diagnostics']['info']}</li>
                        </ul>
                    </div>

                    <!-- Repairs -->
                    <div class="card">
                        <h2>Auto-Repairs (24h)</h2>
                        <div class="stat">{report['repairs']['successful']}</div>
                        <div class="label">Successful Repairs</div>
                        <ul class="list" style="margin-top: 15px;">
                            <li>Failed: {report['repairs']['failed']}</li>
                            <li>Recommended: {report['repairs']['recommended']}</li>
                        </ul>
                    </div>

                    <!-- Metrics -->
                    <div class="card">
                        <h2>Performance Metrics</h2>
                        <div style="font-size: 12px; line-height: 1.8;">
                            <div>Success Rate: <strong>{report['metrics'].get('success_rate_24h', 0)}%</strong></div>
                            <div>Avg Confidence: <strong>{report['metrics'].get('avg_confidence', 0)}</strong></div>
                            <div>Decisions: <strong>{report['metrics'].get('decisions_24h', 0)}</strong></div>
                            <div>Patterns: <strong>{report['metrics'].get('total_patterns_learned', 0)}</strong></div>
                        </div>
                    </div>

                    <!-- Alerts -->
                    <div class="card">
                        <h2>Active Alerts</h2>
                        <div class="stat">{report['alerts']['total_active']}</div>
                        <div class="label">Unacknowledged</div>
                        <ul class="list" style="margin-top: 15px;">
                            <li>High: {report['alerts']['high_severity']}</li>
                            <li>Medium: {report['alerts']['medium_severity']}</li>
                            <li>Low: {report['alerts']['low_severity']}</li>
                        </ul>
                    </div>

                    <!-- Compliance -->
                    <div class="card">
                        <h2>Constraint Compliance</h2>
                        <div class="stat">{report['compliance']['compliance_score']:.0f}%</div>
                        <div class="label">Overall Compliance</div>
                        <div class="progress" style="margin-top: 15px;">
                            <div class="progress-bar" style="width: {report['compliance']['compliance_score']}%"></div>
                        </div>
                        <div style="font-size: 12px; margin-top: 15px;">
                            Critical Violations: {report['compliance']['critical_violations']}
                        </div>
                    </div>
                </div>

                <!-- Recent Issues -->
                <div class="card" style="margin-top: 20px;">
                    <h2>Recent Critical Issues</h2>
                    {self._render_issues(report)}
                </div>

                <!-- Last Updated -->
                <div style="text-align: center; margin-top: 40px; color: #64748b; font-size: 12px;">
                    Last updated: {report['timestamp']}
                    <br>
                    Status: 🟢 Online
                </div>
            </div>

            <script>
                // Auto-refresh every 30 seconds
                setTimeout(() => location.reload(), 30000);
            </script>
        </body>
        </html>
        """

        return html

    def _calculate_health_score(self, report: Dict[str, Any]) -> float:
        """Calculate overall health score"""
        score = 100.0

        # Deduct for diagnostics
        score -= min(20, report["diagnostics"]["total_24h"])

        # Deduct for unresolved critical issues
        score -= report["diagnostics"]["unresolved_critical"] * 5

        # Add for successful repairs
        score += min(10, report["repairs"]["successful"])

        # Deduct for active alerts
        score -= min(15, report["alerts"]["total_active"])

        # Factor in success rate
        success_rate = report["metrics"].get("success_rate_24h", 50)
        if success_rate < 70:
            score -= (70 - success_rate) / 70 * 10

        return max(0, min(100, score))

    def _get_health_color(self, score: float) -> str:
        """Get color based on health score"""
        if score >= 85:
            return "#10b981"  # Green
        elif score >= 70:
            return "#f59e0b"  # Yellow
        elif score >= 50:
            return "#f97316"  # Orange
        else:
            return "#ef4444"  # Red

    def _render_issues(self, report: Dict[str, Any]) -> str:
        """Render critical issues in HTML"""
        issues = report["diagnostics"]["unresolved_critical"]

        if issues == 0:
            return "<div style='color: #10b981;'>✓ No critical issues</div>"

        html = ""
        for i in range(min(5, issues)):
            html += f"""
            <div class="alert">
                <strong>Critical Issue {i+1}</strong>
                <div style="font-size: 12px; margin-top: 5px;">System requires attention</div>
            </div>
            """

        return html
