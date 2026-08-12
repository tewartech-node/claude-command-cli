"""
Brain Dashboard: Central control and visualization
Real-time view of network status, decisions, and learning
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, jsonify, render_template_string
import os

app = Flask(__name__)

DB_PATH = os.getenv("DB_PATH", "./agent/storage/memory.db")


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def dashboard():
    """Main dashboard page"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>The Brain Network Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0f172a;
                color: #e2e8f0;
                padding: 20px;
            }
            .container { max-width: 1400px; margin: 0 auto; }
            h1 { margin-bottom: 30px; color: #60a5fa; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 20px;
            }
            .card h2 { color: #60a5fa; font-size: 16px; margin-bottom: 15px; }
            .stat { font-size: 32px; font-weight: bold; color: #10b981; }
            .label { color: #94a3b8; font-size: 12px; text-transform: uppercase; }
            .list { list-style: none; }
            .list li { padding: 8px 0; border-bottom: 1px solid #334155; }
            .list li:last-child { border-bottom: none; }
            .progress {
                background: #334155;
                height: 8px;
                border-radius: 4px;
                overflow: hidden;
                margin-top: 10px;
            }
            .progress-bar {
                background: linear-gradient(90deg, #60a5fa, #10b981);
                height: 100%;
                transition: width 0.3s;
            }
            .status {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .status.online { background: #10b981; }
            .status.offline { background: #ef4444; }
            .status.idle { background: #f59e0b; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧠 The Brain Network Dashboard</h1>

            <div class="grid">
                <!-- Brain Status -->
                <div class="card">
                    <h2>Brain Status</h2>
                    <div class="stat" id="brain-status">●</div>
                    <div class="label">System Status</div>
                    <div style="margin-top: 15px; font-size: 12px;">
                        <div>Decisions: <span id="decisions-count">-</span></div>
                        <div>Uptime: <span id="uptime">-</span></div>
                    </div>
                </div>

                <!-- Performance -->
                <div class="card">
                    <h2>Performance</h2>
                    <div class="label">Success Rate (Last 24h)</div>
                    <div class="stat" id="success-rate">-</div>
                    <div class="progress">
                        <div class="progress-bar" id="success-bar" style="width: 0%"></div>
                    </div>
                </div>

                <!-- Network Status -->
                <div class="card">
                    <h2>Network Devices</h2>
                    <ul class="list" id="network-devices">
                        <li>Loading...</li>
                    </ul>
                </div>

                <!-- Email Activity -->
                <div class="card">
                    <h2>📧 Email Activity</h2>
                    <div class="label">Last 24 Hours</div>
                    <div class="stat" id="email-count">-</div>
                    <ul class="list" id="top-senders"></ul>
                </div>

                <!-- Traffic Patterns -->
                <div class="card">
                    <h2>🌐 Web Activity</h2>
                    <div class="label">Top Interests</div>
                    <ul class="list" id="interests"></ul>
                </div>

                <!-- Learning Progress -->
                <div class="card">
                    <h2>Learning Progress</h2>
                    <div class="label">Patterns Learned</div>
                    <div class="stat" id="patterns-count">-</div>
                    <div style="margin-top: 15px; font-size: 12px;">
                        <div>Confidence: <span id="avg-confidence">-</span>%</div>
                        <div>Feedback Rate: <span id="feedback-rate">-</span>%</div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            async function updateDashboard() {
                try {
                    const response = await fetch('/api/stats');
                    const data = await response.json();

                    // Update stats
                    document.getElementById('brain-status').textContent = '●';
                    document.getElementById('decisions-count').textContent = data.total_decisions || 0;
                    document.getElementById('uptime').textContent = data.uptime || 'N/A';
                    document.getElementById('success-rate').textContent = data.success_rate + '%' || '0%';
                    document.getElementById('success-bar').style.width = (data.success_rate || 0) + '%';
                    document.getElementById('email-count').textContent = data.email_count || 0;
                    document.getElementById('patterns-count').textContent = data.patterns || 0;
                    document.getElementById('avg-confidence').textContent = Math.round(data.confidence * 100) || '0';
                    document.getElementById('feedback-rate').textContent = data.feedback_rate || '0';

                    // Update devices
                    if (data.devices) {
                        document.getElementById('network-devices').innerHTML =
                            data.devices.map(d => `
                                <li>
                                    <span class="status ${'online'}"></span>
                                    ${d.name}
                                </li>
                            `).join('');
                    }

                    // Update senders
                    if (data.top_senders) {
                        document.getElementById('top-senders').innerHTML =
                            data.top_senders.map(s => `<li>${s.sender}: ${s.count}</li>`).join('');
                    }

                    // Update interests
                    if (data.interests) {
                        document.getElementById('interests').innerHTML =
                            data.interests.map(i => `<li>${i.topic}</li>`).join('');
                    }
                } catch (e) {
                    console.error('Dashboard update error:', e);
                }
            }

            // Update every 5 seconds
            updateDashboard();
            setInterval(updateDashboard, 5000);
        </script>
    </body>
    </html>
    """)


@app.route("/api/stats")
def api_stats():
    """Get dashboard statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get decision stats
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
            FROM decisions
        """)
        d_total, d_success = cursor.fetchone()
        success_rate = (d_success / d_total * 100) if d_total > 0 else 0

        # Get email activity
        cursor.execute("""
            SELECT COUNT(*) FROM email_activity
            WHERE timestamp > datetime('now', '-1 day')
        """)
        email_count = cursor.fetchone()[0]

        # Get top senders
        cursor.execute("""
            SELECT sender_email, message_count FROM email_senders
            ORDER BY message_count DESC LIMIT 3
        """)
        top_senders = [{"sender": row[0], "count": row[1]} for row in cursor.fetchall()]

        # Get interests
        cursor.execute("""
            SELECT interest_category FROM browsing_interests
            ORDER BY frequency DESC LIMIT 5
        """)
        interests = [{"topic": row[0]} for row in cursor.fetchall()]

        # Get patterns
        cursor.execute("SELECT COUNT(*) FROM patterns")
        patterns = cursor.fetchone()[0]

        # Get confidence
        cursor.execute("""
            SELECT AVG(CASE WHEN rating >= 4 THEN 1.0 ELSE 0 END)
            FROM ratings
        """)
        confidence = cursor.fetchone()[0] or 0.5

        # Get feedback rate
        cursor.execute("""
            SELECT COUNT(DISTINCT decision_id) as rated FROM ratings
        """)
        rated = cursor.fetchone()[0]
        feedback_rate = (rated / d_total * 100) if d_total > 0 else 0

        conn.close()

        return jsonify({
            "total_decisions": d_total,
            "success_rate": round(success_rate, 1),
            "email_count": email_count,
            "top_senders": top_senders,
            "interests": interests,
            "patterns": patterns,
            "confidence": confidence,
            "feedback_rate": round(feedback_rate, 1),
            "devices": [
                {"name": "Main Brain", "status": "online"},
                {"name": "Email Monitor", "status": "online"},
                {"name": "Traffic Monitor", "status": "online"},
            ],
            "uptime": "24h"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
