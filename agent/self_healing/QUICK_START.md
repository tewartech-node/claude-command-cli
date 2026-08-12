# Self-Healing System Quick Start

Get your self-healing system running in 5 minutes.

## Installation

The self-healing module is built-in. No extra dependencies needed beyond what Brain already requires.

```bash
cd claude-command-cli
python -m agent.self_healing.cli --help
```

## Basic Usage

### 1. Run a Full System Diagnostic

```bash
python -m agent.self_healing.cli diagnose --full
```

Shows all health issues in your system:
- Performance (CPU, memory, disk)
- Database integrity
- Code quality
- Learning progress
- Network connectivity

### 2. Run Automatic Repairs

```bash
python -m agent.self_healing.cli repair --auto
```

System automatically fixes:
- Database fragmentation (VACUUM)
- Old data archival (>90 days)
- Bare except clauses
- Memory issues
- Performance problems

### 3. Check System Status

```bash
python -m agent.self_healing.cli status
```

Quick overview:
- Health score
- Diagnostics found
- Repairs made
- Active alerts
- Key metrics

### 4. Start Monitoring

```bash
python -m agent.self_healing.cli monitor --status
```

Real-time monitoring:
- Success rate tracking
- Confidence levels
- Anomaly detection
- Metric collection

### 5. View Health Dashboard

```bash
python -m agent.self_healing.cli dashboard --health
```

Or generate HTML:
```bash
python -m agent.self_healing.cli dashboard --html dashboard.html
# Open dashboard.html in browser
```

## Python Integration

Use directly in your code:

```python
from agent.self_healing import (
    DiagnosticEngine,
    SelfRepairEngine,
    BehaviorMonitor,
    HealthDashboard
)

# Run diagnostics
diagnostic = DiagnosticEngine()
issues = diagnostic.full_diagnostic_scan()

# Auto-repair
repair = SelfRepairEngine()
fixes = repair.full_repair_cycle()

# Monitor health
monitor = BehaviorMonitor()
monitor.start_monitoring()

# View dashboard
dashboard = HealthDashboard()
report = dashboard.get_comprehensive_health_report()

print(f"Health: {report['metrics']['success_rate_24h']}%")
print(f"Alerts: {report['alerts']['total_active']}")
```

## Common Commands

```bash
# Analyze codebase
python -m agent.self_healing.cli analyze --full

# Check constraints
python -m agent.self_healing.cli constraints --check-all

# Create checkpoint
python -m agent.self_healing.cli version --checkpoint

# See commit history
python -m agent.self_healing.cli version --history

# Rollback to known good state
python -m agent.self_healing.cli version --rollback abc123def

# Tag stable version
python -m agent.self_healing.cli version --tag stable-v1.0
```

## Automated Daily Check

Add to your crontab:

```bash
# Every 6 hours
0 */6 * * * cd /path/to/claude-command-cli && python -m agent.self_healing.cli repair --auto

# Every morning
0 9 * * * cd /path/to/claude-command-cli && python -m agent.self_healing.cli diagnose --full
```

## Dashboard Visualization

Serve health dashboard on web:

```python
from flask import Flask
from agent.self_healing import HealthDashboard

app = Flask(__name__)
dashboard = HealthDashboard()

@app.route("/health")
def health():
    return dashboard.get_dashboard_html()

# python app.py
# Visit http://localhost:5000/health
```

## What It Watches

### Performance
- CPU usage (<80%)
- Memory usage (<500MB)
- Disk space (>10% free)
- Response latency

### Learning
- Success rate (>70%)
- Confidence levels (>0.5)
- Pattern extraction (>1/day)
- Decision velocity (>1/hour)

### Code Quality
- No security issues
- No dead code
- Proper error handling
- Code complexity <10

### Data Integrity
- Database integrity OK
- No corruption
- Reasonable size (<1GB)
- No fragmentation

## What It Fixes

### Automatic
- Database fragmentation → VACUUM
- Large database → Archive old data
- Bare except clauses → Proper handlers
- High memory → Reduce buffers
- High CPU → Throttle tasks

### Recommended
- Code refactoring
- Memory optimization
- Architecture changes
- Dependency updates

## Rollback to Safety

If something goes wrong:

```bash
# See recent commits
python -m agent.self_healing.cli version --history

# Go back to known good state
python -m agent.self_healing.cli version --rollback abc123def
```

All repairs are logged with rollback capability.

## Configuration

Set environment variables:

```bash
# Enable/disable auto-repair (default: true)
export AUTO_REPAIR=true

# Database path
export DB_PATH=./agent/storage/memory.db

# Alert sensitivity (0-1, default: 0.7)
export ALERT_THRESHOLD=0.7

# Monitoring interval (seconds, default: 60)
export MONITOR_INTERVAL=60
```

## Troubleshooting

### "Database locked" error
- Another process is accessing database
- Wait a moment and retry
- Or: stop Brain, run repair, restart Brain

### "Git not available"
- Install git: `apt-get install git`
- Or disable version manager

### False positive alerts
- Increase ALERT_THRESHOLD (less sensitive)
- Update baseline: delete old metrics from database

### Repair not applied
- Check if AUTO_REPAIR=true
- Review repair log in database
- Manually rollback and try again

## Success Indicators

System is working well when:
- ✅ Health score stays >85%
- ✅ Success rate >85%
- ✅ Auto-repairs succeed >80% of the time
- ✅ No unresolved critical issues
- ✅ All constraints satisfied

## Next Steps

1. **Run diagnostics** to see current state
2. **Let it auto-repair** for 24 hours
3. **Review repair log** to understand what was fixed
4. **Adjust thresholds** based on your needs
5. **Enable on production** for autonomous operation

## Support

For issues or questions:

1. Check SELF_HEALING_GUIDE.md for detailed docs
2. Review diagnostic scan output
3. Check repair log in database
4. See commit history for what changed

---

Ready? Start with:
```bash
python -m agent.self_healing.cli status
```

🚀 Your system is now self-healing!
